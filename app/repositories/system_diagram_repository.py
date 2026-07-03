"""
Repository for system diagram database operations.
"""
from typing import Optional
from supabase import Client
from app.models.system_diagram import SystemDiagram
from app.core.logging import logger


class SystemDiagramRepository:
    """Handle system diagram database operations"""

    def __init__(self, client: Client):
        self.client = client

    def get_by_system(self, system: str) -> Optional[SystemDiagram]:
        """
        Get diagram for a vehicle system.

        Performs case-insensitive exact match on system name.

        Args:
            system: System name (e.g., "catalytic converter")

        Returns:
            SystemDiagram if found, None otherwise
        """
        try:
            response = (
                self.client.table("system_diagrams")
                .select("*")
                .ilike("system", system)  # Case-insensitive
                .limit(1)
                .execute()
            )

            if response.data:
                return SystemDiagram.from_dict(response.data[0])

            return None

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
        try:
            response = (
                self.client.table("system_diagrams")
                .select("*")
                .execute()
            )

            if response.data:
                for record in response.data:
                    record_system = record['system'].lower()
                    # Check if search term is in record system name
                    if system_lower in record_system:
                        logger.info(
                            "system_diagram_found",
                            system=system,
                            matched_system=record['system'],
                            match_type="substring"
                        )
                        return SystemDiagram.from_dict(record)

                    # Check if record system is in search term
                    if record_system in system_lower:
                        logger.info(
                            "system_diagram_found",
                            system=system,
                            matched_system=record['system'],
                            match_type="contains"
                        )
                        return SystemDiagram.from_dict(record)

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

        Args:
            system: System name (lowercase)

        Returns:
            List of synonyms to try
        """
        # Map common variations
        synonym_map = {
            # Catalytic converter variations
            "catalyst": ["catalytic converter", "catalyst system"],
            "cat converter": ["catalytic converter"],
            "catalytic converter system": ["catalytic converter"],

            # O2 sensor variations
            "o2 sensor": ["oxygen sensor", "o2 sensor"],
            "oxygen sensor": ["o2 sensor", "oxygen sensor"],
            "lambda sensor": ["oxygen sensor", "o2 sensor"],

            # EGR variations
            "egr": ["egr valve", "exhaust gas recirculation"],
            "egr valve": ["egr", "exhaust gas recirculation"],
            "exhaust gas recirculation": ["egr valve", "egr"],

            # MAF variations
            "maf": ["mass air flow", "maf sensor"],
            "mass air flow": ["maf", "maf sensor"],
            "maf sensor": ["mass air flow", "maf"],

            # Fuel system variations
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

        return synonym_map.get(system, [])
