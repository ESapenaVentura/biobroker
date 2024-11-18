import datetime
from enum import Enum
from dateutil import parser
from typing import Dict, Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict

"""
FIELDS/SUPPORTING MODELS
------------------------
"""


class CharacteristicsFields(BaseModel):
    model_config = ConfigDict(extra='forbid')
    text: str | datetime.datetime | int | float
    unit: Optional[str] = None
    ontologyTerms: Optional[list[str]] = None
    tag : Optional[str] = None

    @field_validator('text')
    @classmethod
    def proper_formats(cls, value):
        """
        Evaluate if an input is a date/int/float and give it a proper formatting, returning it as str
        """
        if isinstance(value, datetime.datetime):
            value = value.strftime("%Y-%m-%dT%H:%M:%SZ")
            if value.endswith('T00:00:00Z'):
                value = value.replace('T00:00:00Z', '')
            return value
        elif isinstance(value, float):
            return str(int(value)) if value.is_integer() else str(value)
        return str(value)

class DataContent(BaseModel):
    value: str

class DataEntry(BaseModel):
    webinSubmissionAccountId: str = Field(pattern="Webin-[0-9]+$")
    type: str
    content: list[Dict[str, DataContent]]

class RelationshipType(str, Enum):
    derived_from = "derived_from"
    same_as = "same_as"
    has_member = "has_member"
    child_of = "child_of"

class Relationship(BaseModel):
    model_config = ConfigDict(extra='forbid')
    target: str = Field(pattern="^SAMEA[0-9]+$")
    source: str = Field(pattern="^SAMEA[0-9]+$")
    type: RelationshipType

class Organization(BaseModel):
    Name: str

class ExternalUrl(BaseModel):
    url: str = Field(pattern="https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}([-a-zA-Z0-9()@:%_\+.~#?&\/=]*)")
    doi: Optional[str] = None

"""
DATA MODELS
-----------
"""

class StructuredDataModel(BaseModel):
    """
    Biosamples' structured data model
    """
    accession: str = Field(pattern="^SAME.[0-9]+$")
    data: list[DataEntry]

class BiosampleGeneralModel(BaseModel):
    """
    Biosamples General model
    """
    model_config = ConfigDict(extra='allow')
    name: str = Field(min_length=1)
    accession: Optional[str] = None
    release: str
    characteristics: Dict[str, list[CharacteristicsFields]]
    relationships: Optional[list[Relationship]] = None
    organization: Optional[list[Organization]] = None
    structuredData: Optional[list[DataEntry]] = None
    externalReferences: Optional[list[ExternalUrl]] = None

    @field_validator('release')
    @classmethod
    def parse_date(cls, value):
        try:
            value = parser.isoparse(value).strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            raise ValueError("Invalid date format. Should be provided as YYYY-MM-DD with optional Thh:mm:ss.sssZ") from None
        return value

    @field_validator('characteristics')
    @classmethod
    def organism_must_be_set(cls, value):
        valid_organism_keys = ('organism', 'Organism', 'species', 'Species')
        try:
            which_one = [key in value for key in valid_organism_keys]
            which_one.index(True)
        except ValueError:
            raise ValueError("'organism' must be set. Please use the keys 'organism', 'Organism', 'species' or 'Species'") from None
        value['organism'] = value[valid_organism_keys[which_one.index(True)]]
        for organism_key in valid_organism_keys[1:]:
            if organism_key in value:
                del value[organism_key]
        return value