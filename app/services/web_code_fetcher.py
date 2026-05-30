"""
Web Code Fetcher Service
Fetches OBD codes from free online sources when not found in local database.
"""

import httpx
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any
import re
from app.core.logging import logger


class WebCodeFetcher:
    """Fetches OBD code information from free online sources"""

    def __init__(self):
        self.sources = [
            {
                "name": "OBD-Codes.com",
                "url_template": "https://www.obd-codes.com/{}",
                "parser": self._parse_obd_codes_com
            },
            {
                "name": "Engine-Codes.com",
                "url_template": "https://www.engine-codes.com/{}",
                "parser": self._parse_engine_codes_com
            }
        ]
        self.timeout = 10  # seconds

    async def fetch_code(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Fetch OBD code information from online sources.

        Args:
            code: OBD code (e.g., "P3499")

        Returns:
            Dictionary with code information or None if not found
        """
        code = code.upper().strip()

        logger.info("web_fetch_started", code=code)

        # Try each source in order
        for source in self.sources:
            try:
                result = await self._fetch_from_source(code, source)
                if result:
                    logger.info(
                        "web_fetch_success",
                        code=code,
                        source=source["name"]
                    )
                    return result
            except Exception as e:
                logger.warning(
                    "web_fetch_failed",
                    code=code,
                    source=source["name"],
                    error=str(e)
                )
                continue

        logger.warning("web_fetch_no_results", code=code)
        return None

    async def _fetch_from_source(
        self,
        code: str,
        source: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Fetch from a specific source"""

        url = source["url_template"].format(code.lower())

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, follow_redirects=True)

            if response.status_code != 200:
                return None

            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Use source-specific parser
            return source["parser"](soup, code)

    def _parse_obd_codes_com(
        self,
        soup: BeautifulSoup,
        code: str
    ) -> Optional[Dict[str, Any]]:
        """Parse OBD-Codes.com HTML"""

        try:
            # Extract description
            description = None

            # Try common selectors for description
            for selector in ['h1', '.code-description', 'meta[name="description"]']:
                elem = soup.select_one(selector)
                if elem:
                    text = elem.get('content') if elem.name == 'meta' else elem.get_text()
                    if text and code in text.upper():
                        description = text.replace(code, '').strip(' -:')
                        break

            if not description:
                return None

            # Extract symptoms
            symptoms = self._extract_section(soup, ['symptom', 'sign', 'indicator'])

            # Extract causes
            causes = self._extract_section(soup, ['cause', 'reason', 'problem'])

            # Extract fixes
            fixes = self._extract_section(soup, ['fix', 'repair', 'solution', 'diagnostic'])

            return {
                "code": code,
                "description": description,
                "symptoms": symptoms or "Check engine light on",
                "common_causes": causes or "Faulty component, wiring issue, sensor malfunction",
                "generic_fixes": fixes or "Diagnose with scanner, check wiring, test components",
                "source": "OBD-Codes.com",
                "raw_url": soup.find('meta', property='og:url')['content'] if soup.find('meta', property='og:url') else None
            }

        except Exception as e:
            logger.error("parse_error", error=str(e), source="obd-codes.com")
            return None

    def _parse_engine_codes_com(
        self,
        soup: BeautifulSoup,
        code: str
    ) -> Optional[Dict[str, Any]]:
        """Parse Engine-Codes.com HTML"""

        try:
            # Extract description from title or heading
            description = None
            title = soup.find('title')
            if title:
                text = title.get_text()
                if code in text.upper():
                    description = text.replace(code, '').strip(' -:|')

            if not description:
                h1 = soup.find('h1')
                if h1:
                    description = h1.get_text().replace(code, '').strip(' -:')

            if not description:
                return None

            # Extract other sections
            symptoms = self._extract_section(soup, ['symptom'])
            causes = self._extract_section(soup, ['cause', 'possible cause'])
            fixes = self._extract_section(soup, ['fix', 'repair', 'how to'])

            return {
                "code": code,
                "description": description,
                "symptoms": symptoms or "Check engine light on",
                "common_causes": causes or "Component failure, wiring issue, sensor fault",
                "generic_fixes": fixes or "Diagnose with scanner, inspect wiring, test components",
                "source": "Engine-Codes.com",
                "raw_url": None
            }

        except Exception as e:
            logger.error("parse_error", error=str(e), source="engine-codes.com")
            return None

    def _extract_section(
        self,
        soup: BeautifulSoup,
        keywords: list[str]
    ) -> Optional[str]:
        """Extract a section based on keywords"""

        # Look for headings containing keywords
        for keyword in keywords:
            # Find heading
            heading = soup.find(
                ['h2', 'h3', 'h4', 'strong', 'b'],
                string=re.compile(keyword, re.IGNORECASE)
            )

            if heading:
                # Get the content after the heading
                content_parts = []

                # Get next siblings until next heading
                for sibling in heading.find_next_siblings():
                    if sibling.name in ['h2', 'h3', 'h4']:
                        break

                    text = sibling.get_text().strip()
                    if text and len(text) > 10:
                        content_parts.append(text)

                if content_parts:
                    return ' '.join(content_parts[:3])  # First 3 paragraphs

        return None

    def extract_code_info_simple(self, html: str, code: str) -> Dict[str, Any]:
        """
        Simple extraction for when parsers fail.
        Extracts basic info from plain HTML text.
        """

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'\s+', ' ', text).strip()

        # Try to find description near the code
        pattern = rf'{code}[:\s-]+([^.]+\.)'
        match = re.search(pattern, text, re.IGNORECASE)

        description = "Generic OBD-II diagnostic trouble code"
        if match:
            description = match.group(1).strip()

        return {
            "code": code,
            "description": description,
            "symptoms": "Check engine light on, possible performance issues",
            "common_causes": "Component malfunction, sensor fault, wiring issue",
            "generic_fixes": "Scan for related codes, inspect wiring, test components",
            "source": "web_scraped",
            "raw_url": None
        }
