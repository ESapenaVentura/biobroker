from enum import Enum
from dateutil import parser
from typing import Dict, Optional, Union

from pydantic import BaseModel, Field, AnyHttpUrl, field_validator, AliasChoices, ConfigDict, RootModel

"""
Data models used to validate metadata entities.
"""

class OntologyTerm(BaseModel):
    ontologyTerm: AnyHttpUrl


class CharacteristicsFields(BaseModel):
    model_config = ConfigDict(extra='forbid')
    text: str
    unit: Optional[str] = None
    ontologyTerms: Optional[list[OntologyTerm]] = None

class DataContent(BaseModel):
    value: str

class DataEntry(BaseModel):
    webinSubmissionAccountId: str = Field(pattern="Webin-[0-9]+$")
    type: str
    content: list[Dict[str, DataContent]]

class StructuredDataModel(BaseModel):
    """
    Biosamples' structured data model
    """
    accession: str = Field(pattern="^SAME.[0-9]+$")
    data: list[DataEntry]

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
    organization: Optional[list[Dict]] = None
    structuredData: Optional[StructuredDataModel] = None

    @field_validator('release')
    @classmethod
    def parse_date(cls, value):
        try:
            value = parser.isoparse(value).strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError as e:
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
