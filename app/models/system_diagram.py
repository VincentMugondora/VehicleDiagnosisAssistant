"""
System diagram data model.

Represents educational diagrams for vehicle systems.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class SystemDiagram:
    """
    Educational diagram for a vehicle system.

    Attributes:
        id: Unique identifier
        system: Vehicle system name (e.g., "catalytic converter")
        image_url: Public HTTPS URL to diagram image
        source: Image source (e.g., "Wikimedia Commons")
        license: Image license (e.g., "CC BY-SA 4.0")
        attribution_text: Optional attribution line for text diagnosis
        caption: Short caption for WhatsApp (<60 chars recommended)
        created_at: When record was created
        updated_at: When record was last updated
    """
    id: str
    system: str
    image_url: str
    source: str
    license: str
    attribution_text: Optional[str]
    caption: Optional[str]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_dict(cls, data: dict) -> 'SystemDiagram':
        """Create SystemDiagram from database record"""
        return cls(
            id=data['id'],
            system=data['system'],
            image_url=data['image_url'],
            source=data['source'],
            license=data['license'],
            attribution_text=data.get('attribution_text'),
            caption=data.get('caption'),
            created_at=data['created_at'] if isinstance(data['created_at'], datetime)
                      else datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')),
            updated_at=data['updated_at'] if isinstance(data['updated_at'], datetime)
                      else datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
        )
