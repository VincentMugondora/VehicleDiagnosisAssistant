"""
Repository for system diagram database operations.
"""
from typing import Optional
from supabase import Client
from app.models.system_diagram import SystemDiagram
from app.core.logging import logger

# Global cache for diagram lookups (reduces 0.6s query to <1ms)
_diagram_cache = {}
_all_diagrams_cache = None


# ============================================================================
# SYSTEM NAME SYNONYM MAP
# ============================================================================
# Maps common variations and abbreviations to canonical system names.
# Add new entries here when adding diagrams for systems with multiple names.
#
# Format: "search_term": ["canonical_system_name_1", "canonical_system_name_2"]
# ============================================================================

SYSTEM_SYNONYMS = {
    # Catalytic converter variations
    "catalyst": ["catalytic converter", "catalyst system"],
    "cat": ["catalytic converter"],  # Common abbreviation
    "cat converter": ["catalytic converter"],
    "catalytic converter system": ["catalytic converter"],

    # O2 sensor variations
    "o2 sensor": ["oxygen sensor", "o2 sensor"],
    "o2": ["oxygen sensor"],  # Common abbreviation
    "oxygen sensor": ["o2 sensor", "oxygen sensor"],
    "lambda sensor": ["oxygen sensor", "o2 sensor"],

    # EGR variations
    "egr": ["egr valve", "exhaust gas recirculation"],
    "egr valve": ["egr", "exhaust gas recirculation"],
    "exhaust gas recirculation": ["egr valve", "egr"],

    # MAF variations
    "maf": ["mass air flow sensor"],  # Fixed: point to correct system name
    "mass air flow": ["mass air flow sensor"],
    "mass air flow sensor": ["mass air flow"],
    "maf sensor": ["mass air flow sensor"],

    # Fuel system variations
    "fuel": ["fuel injector", "fuel pump"],  # Common abbreviation maps to both fuel systems
    "fuel system": ["fuel injector", "fuel pump"],
    "fuel injector": ["fuel system", "fuel injection"],
    "fuel pump": ["fuel system"],

    # Ignition variations
    "ignition": ["ignition coil", "spark plug"],
    "ignition coil": ["ignition", "ignition system"],
    "spark plug": ["ignition", "ignition system"],

    # Evaporative system
    "evap": ["evaporative emission", "evap system"],
    "evaporative emission": ["evap", "evap system"],
    "evap system": ["evaporative emission", "evap"],

    # Transmission
    "transmission": ["transmission system", "gearbox"],
    "gearbox": ["transmission"],

    # Cooling system
    "cooling": ["cooling system", "coolant"],
    "coolant": ["cooling system", "cooling"],
    "thermostat": ["cooling system"],

    # Throttle
    "throttle": ["throttle body", "throttle position"],
    "throttle body": ["throttle", "throttle position"],

    # Air intake
    "air intake": ["intake manifold", "intake system"],
    "intake": ["air intake", "intake manifold"],
}

# ============================================================================
# END SYNONYM MAP
# ============================================================================


class SystemDiagramRepository:
    """Handle system diagram database operations"""

    def __init__(self, client: Client):
        self.client = client

    def get_by_system(self, system: str) -> Optional[SystemDiagram]:
        """
        Get diagram for a vehicle system with caching.

        Performs case-insensitive exact match on system name.

        Args:
            system: System name (e.g., "catalytic converter")

        Returns:
            SystemDiagram if found, None otherwise
        """
        # Check cache first
        system_lower = system.lower().strip()
        if system_lower in _diagram_cache:
            return _diagram_cache[system_lower]

        try:
            response = (
                self.client.table("system_diagrams")
                .select("*")
                .ilike("system", system)  # Case-insensitive
                .limit(1)
                .execute()
            )

            diagram = None
            if response.data:
                diagram = SystemDiagram.from_dict(response.data[0])

            # Cache result (even None)
            _diagram_cache[system_lower] = diagram
            return diagram

        except Exception as e:
            logger.error(
                "system_diagram_lookup_failed",
                system=system,
                error=str(e)
            )
            return None

    def get_by_system_fuzzy(self, system: str) -> Optional[SystemDiagram]:
        """
        Get diagram with fuzzy matching.

        Tries multiple strategies:
        1. Exact match (case-insensitive)
        2. Substring match (e.g., "catalyst" matches "catalytic converter")
        3. Synonym match (common variations)

        Args:
            system: System name

        Returns:
            SystemDiagram if found, None otherwise
        """
        # Normalize system name
        system_lower = system.lower().strip()

        # Strategy 1: Exact match
        exact = self.get_by_system(system)
        if exact:
            logger.info(
                "system_diagram_found",
                system=system,
                match_type="exact"
            )
            return exact

        # Strategy 2: Check for common synonyms/variations
        synonyms = self._get_synonyms(system_lower)
        for synonym in synonyms:
            result = self.get_by_system(synonym)
            if result:
                logger.info(
                    "system_diagram_found",
                    system=system,
                    matched_system=synonym,
                    match_type="synonym"
                )
                return result

        # Strategy 3: Substring match (system name contains search term)
        # Require minimum search length to avoid overly generic matches
        MIN_SEARCH_LENGTH = 5

        if len(system_lower) < MIN_SEARCH_LENGTH:
            logger.debug(
                "substring_match_skipped",
                system=system,
                reason=f"search_term_too_short (< {MIN_SEARCH_LENGTH} chars)"
            )
            return None

        try:
            response = (
                self.client.table("system_diagrams")
                .select("*")
                .execute()
            )

            if response.data:
                # Collect all matches with scores for specificity
                matches = []

                for record in response.data:
                    record_system = record['system'].lower()

                    # Check if search term is in record system name
                    if system_lower in record_system:
                        # Score by specificity (longer search term relative to system name = more specific)
                        specificity_score = len(system_lower) / len(record_system)
                        matches.append((specificity_score, record, "substring"))

                    # Check if record system is in search term
                    elif record_system in system_lower:
                        # Lower score for "contains" matches (less specific)
                        specificity_score = len(record_system) / len(system_lower)
                        matches.append((specificity_score, record, "contains"))

                # Return most specific match
                if matches:
                    # Sort by score (highest = most specific)
                    matches.sort(key=lambda x: x[0], reverse=True)
                    best_score, best_record, match_type = matches[0]

                    logger.info(
                        "system_diagram_found",
                        system=system,
                        matched_system=best_record['system'],
                        match_type=match_type,
                        specificity_score=f"{best_score:.2f}",
                        num_candidates=len(matches)
                    )
                    return SystemDiagram.from_dict(best_record)

        except Exception as e:
            logger.error(
                "system_diagram_fuzzy_search_failed",
                system=system,
                error=str(e)
            )

        # No match found
        logger.debug(
            "system_diagram_not_found",
            system=system
        )
        return None

    def _get_synonyms(self, system: str) -> list[str]:
        """
        Get common synonyms/variations for a system name.

        Uses the SYSTEM_SYNONYMS constant defined at top of file.

        Args:
            system: System name (lowercase)

        Returns:
            List of synonyms to try
        """
        return SYSTEM_SYNONYMS.get(system, [])

    def insert(
        self,
        system: str,
        image_url: str,
        source: str,
        license: str,
        attribution_text: Optional[str] = None,
        caption: Optional[str] = None
    ) -> Optional[SystemDiagram]:
        """
        Insert a new system diagram.

        Args:
            system: System name (will be normalized to lowercase)
            image_url: Public HTTPS URL to diagram image
            source: Image source (e.g., "Wikimedia Commons")
            license: Image license (e.g., "CC BY-SA 4.0")
            attribution_text: Optional attribution line
            caption: Optional short caption

        Returns:
            SystemDiagram if successful, None on error
        """
        try:
            data = {
                'system': system.lower().strip(),
                'image_url': image_url,
                'source': source,
                'license': license,
                'attribution_text': attribution_text,
                'caption': caption
            }

            response = (
                self.client.table("system_diagrams")
                .insert(data)
                .execute()
            )

            if response.data:
                logger.info(
                    "system_diagram_inserted",
                    system=system
                )
                return SystemDiagram.from_dict(response.data[0])

            return None

        except Exception as e:
            logger.error(
                "system_diagram_insert_failed",
                system=system,
                error=str(e)
            )
            return None

    def upsert(
        self,
        system: str,
        image_url: str,
        source: str,
        license: str,
        attribution_text: Optional[str] = None,
        caption: Optional[str] = None
    ) -> Optional[SystemDiagram]:
        """
        Insert or update a system diagram.

        Uses system name as unique key (case-insensitive).

        Args:
            system: System name (will be normalized to lowercase)
            image_url: Public HTTPS URL to diagram image
            source: Image source (e.g., "Wikimedia Commons")
            license: Image license (e.g., "CC BY-SA 4.0")
            attribution_text: Optional attribution line
            caption: Optional short caption

        Returns:
            SystemDiagram if successful, None on error
        """
        try:
            data = {
                'system': system.lower().strip(),
                'image_url': image_url,
                'source': source,
                'license': license,
                'attribution_text': attribution_text,
                'caption': caption
            }

            response = (
                self.client.table("system_diagrams")
                .upsert(data, on_conflict='system')
                .execute()
            )

            if response.data:
                logger.info(
                    "system_diagram_upserted",
                    system=system
                )
                return SystemDiagram.from_dict(response.data[0])

            return None

        except Exception as e:
            logger.error(
                "system_diagram_upsert_failed",
                system=system,
                error=str(e)
            )
            return None
