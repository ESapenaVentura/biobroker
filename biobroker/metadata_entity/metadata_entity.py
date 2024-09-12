import datetime
import json
import re

from typing import Any

from biobroker.metadata_entity.exceptions import NoNameSetError, NameShouldBeStringError, RelationshipInvalidSourceError, \
    RelationshipInvalidTargetError
from biobroker.generic.exceptions import MandatoryFunctionNotSet
from biobroker.generic.logger import set_up_logger


# MONKEY PATCHING JSON ENCODER TO MAKE ENTITIES JSON SERIALIZABLE #
def _default(self, obj):
    return getattr(obj.__class__, "to_json", _default.default)(obj)


_default.default = json.JSONEncoder().default
json.JSONEncoder.default = _default


class GenericEntity:
    """
    Generic definition of metadata entity.

    :param metadata_content: dictionary with the content of the entity
    """
    def __init__(self, metadata_content: dict, verbose: bool = False):
        self.logger = set_up_logger(self, verbose=verbose)
        self._entity = None
        self.entity = metadata_content
        self.validate()

    @property
    def entity(self) -> dict:
        """
        Entity getter.

        :return: self._entity
        """
        return self._entity

    @entity.setter
    def entity(self, metadata_content: dict):
        """
        Setter for the entity property. Must be overridden by subclasses.

        :param metadata_content: Meta
        :return:
        """
        raise MandatoryFunctionNotSet(self.logger)

    @property
    def id(self) -> str:
        """
        id property. Must be overridden by subclasses.

        :return: string with the ID of the entity
        """
        raise MandatoryFunctionNotSet(self.logger)

    @property
    def accession(self) -> str:
        """
        accession property. Must be overridden by subclasses.

        :return: string with the accession of the entity
        """
        raise MandatoryFunctionNotSet(self.logger)

    def validate(self):
        """
        Validate subclass of GenericEntity. Must be overriden by subclasses.
        """
        raise MandatoryFunctionNotSet(self.logger)

    def flatten(self):
        """
        Flatten the .entity, returning a non-nested dictionary.
        """
        raise MandatoryFunctionNotSet(self.logger)

    def __setitem__(self, key: str, value: str):
        """
        Must be overriden by subclasses.
        """
        raise MandatoryFunctionNotSet(self.logger)

    def __delitem__(self, key: str):
        """
        Must be overriden by subclasses.
        """
        raise MandatoryFunctionNotSet(self.logger)

    def __getitem__(self, item: str):
        """
        Must be overriden by subclasses.
        """
        raise MandatoryFunctionNotSet(self.logger)

    def __contains__(self, item):
        """
        Must be overriden by subclasses.
        """
        raise MandatoryFunctionNotSet(self.logger)

    @staticmethod
    def guidelines() -> str:
        """
        Return a printable string with guidelines on how to fill out each entity subclass. Subclasses are not required
        to override this property, but... it does help, so try to be nice :)

        :return: empty string. This is a generic class and should never be used as is!
        """
        return ""

    # DECODER FUNCTIONS - DEFAULTS STR
    def to_json(self):
        return json.loads(json.dumps(self.entity, default=str))


ROOT_PROPERTIES = ['name', 'release', 'relationships', 'accession', 'sraAccession', 'webinSubmissionAccountId',
                   'status', 'update', 'characteristics', 'submittedVia', 'create', '_links', 'submitted', 'taxId',
                   'organization']
"""List of properties that may be present at the root of a BioSamples JSON."""
VALID_TAGS = ['text', 'ontologyTerms', 'unit']
"""List of valid tags for the characteristics"""
VALID_RELATIONSHIPS = ["derived_from", "same_as"]
"""List of valid relationships for samples"""

"""
TODO list
- Read from flattened source - especially, special values such as relationships, which are flattened into derived from, 
  same as, etc
"""


class Biosample(GenericEntity):
    """
    Biosamples metadata entity. Contains the necessary information to process a non-nested JSON into a valid Biosamples
    sample.

    Current known issue: Only setting up and expecting one value for the properties inside characteristics. Well, this
    is because... Biosamples also expects that! No clue why properties are defaulting to arrays.

    :param metadata_content: non-nested dictionary containing the metadata for the sample.
    :param delimiter: optional parameter, used for key delimiters. Used mainly to manage attributes tags, such as
                      'unit' and 'ontologyTerm'. Explained further in
                      :func:`~broker.metadata_entity.biosample.Biosample.__setitem__`, point 4.
    :param verbose: True if logger should be set to INFO. Default WARNING.
    """
    def __init__(self, metadata_content: dict, delimiter: str = "||", verbose: bool = False):
        self.delimiter = delimiter
        super().__init__(metadata_content, verbose)

    @property
    def id(self):
        """
        Return the property 'id', extracting it from the 'name' property. Defaults to an empty string.
        :return:
        """
        return self.entity.get('name', '')

    @property
    def accession(self) -> str:
        """
        Return the property 'accesssion', extracting it from the 'accession'. Defaults to an emtpy string
        :return:
        """
        return self.entity.get('accession', '')

    @GenericEntity.entity.setter
    def entity(self, metadata: dict):
        """
        Setter for the 'entity' property. Sets up a new sample, with the basic 'name' and 'characteristics' properties.

        :param metadata: non-nested dictionary containing the metadata for the sample.
        """
        self._entity = {"name": "", "characteristics": {}}
        for field, value in metadata.items():
            if not value:
                continue
            self[field] = value

    def validate(self):
        """
        Validate the content of the '.entity'. Currently calls the following functions:

        - :func:`_check_name`
        - :func:`_check_release_date`
        """
        self._check_name()
        self._check_release_date()

    def flatten(self) -> dict:
        """
        Flatten the Biosample.entity property and return a non-nested dictionary. This will be mostly used for
        output generation. Please when expanding this function use match-case statements, as they are cleaner and
        easier to understand than else-if.

        TODO: Biosamples have more complex data structures - Need to add those

        :return: flattened dictionary
        """
        sample_json = self.to_json()
        flattened_json = {}
        for key, value in sample_json.items():
            match key:
                case 'relationships':
                    # Relationships are flattened using just the relationship type. Keep it user friendly!
                    flattened_json = self._flatten_relationships(flattened_json, value)
                case 'characteristics':
                    flattened_json = self._flatten_characteristics(flattened_json, sample_json[key])
                case '_links':
                    # No need to flatten the _links. _links are not useful in output generation.
                    pass
                case _:
                    flattened_json[key] = value
        return flattened_json

    def __getitem__(self, item) -> str | int | dict:
        """
        Special method to get values from the Biosample.entity. Tries to obtain it from root and then characteristics;
        raises ValueError if not found.

        :param item: Value of the key to look up for

        :return: Value of the item if found.
        """
        return self.entity.get('characteristics', {}).get(item, [{}])[0] or self.entity.get(item)

    def __delitem__(self, key: str):
        """
        Special method to delete the values from the Biosample.entity.

        :param key: Key to search for for deletion
        :return:
        """
        if key in self.entity.get('characteristics', {}):
            del self.entity['characteristics'][key]
        else:
            del self.entity[key]

    def __setitem__(self, key: str, value: Any):
        """
        This is a special method to set up values to "entity" in a dict-like manner. Each entity can decide to implement
        checks (Depending on the archive needs) or just return "self.entity[key] = value".

        In the Biosamples case, I decided to add 4 checks:

        - First, it evaluates if it's a datetime object. Datetime objects are not jsonable.
        - Second, evaluate if the key is part of the :data:`ROOT_PROPERTIES`. These are set as-is.
        - Third, evaluate if it's a string. If so, evaluate if there are possible units in the string and log it to a
          warning. I tried automatic conversion but that's a mistake - Let the user deal with it.
        - Fourth, tags for the attributes can be set up from the flattened input dictionary. As such, each sample has
          a delimiter set up, and if it's detected, instead of replacing the value, it will add the tag (e.g.
          `{'size': 1, 'size||unit': 'cm'}` will be translated to `{'size': [{'text': 1, 'unit': cm}]}`). Please see
          https://www.ebi.ac.uk/biosamples/docs/references/api/submit#_sample for more information.

        :param key: name of the attribute.
        :param value: value of the attribute.
        """
        # Deal with datetimes - Specific to BioSamples. If anyone knows a cleaner way let me know please!
        if isinstance(value, datetime.datetime):
            value = value.strftime("%Y-%m-%dT%H:%M:%SZ")
            if value.endswith('T00:00:00Z'):
                value = value.replace('T00:00:00Z', '')

        # Root values
        if key in ROOT_PROPERTIES:
            self.entity[key] = value
        # characteristics
        else:
            characteristic = {}
            # Managing the elements of the attributes in characteristics. Check
            # https://www.ebi.ac.uk/biosamples/docs/references/api/submit#_sample
            if self.delimiter in key:
                key, tag_name = key.split(self.delimiter)
                if not self._tag_is_valid(tag_name):
                    self.logger.warning(f"Tag '{tag_name}' on property '{key}' is not a documented valid tag. "
                                        "It may be rejected on submission.")
                characteristic = self.entity['characteristics'].get(key, [{}])[0]
                characteristic[tag_name] = value
            else:
                characteristic['text'] = value

            self.entity['characteristics'][key] = [characteristic]

    def __contains__(self, item: str) -> bool:
        """
        Special method to check if Biosample.entity  contains 'item'.
        :param item: value of the key to check for.
        :return: True if found, False if not found.
        """
        return item in self.entity or item in self.entity.get('characteristics')

    def _check_name(self):
        """
        Check if the object contains a valid name and, if not, raise error. Current checks:

        - Name is set
        - Name is a string
        """
        if not self.id:
            raise NoNameSetError(logger=self.logger, sample_id=self.id)
        if not isinstance(self['name'], str):
            raise NameShouldBeStringError(logger=self.logger, name=self.id)

    def _check_release_date(self):
        """
        Check the release date is set. If not, default the release to today. It's a small price to pay.
        """
        if 'release' not in self:
            self.logger.warning(f"Sample {self.id}: release date was not set. Setting it to right now.")
            self['release'] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    def add_relationship(self, source, target, relationship):
        """
        Add a relationship to the entity. Source must be the entity's accession; target must be a valid BioSamples
        accession; relationship must be a valid relationship.

        :param source: source entity accession (Must be equal to entity)
        :param target: target sample accession
        :param relationship: Relationship between source and target. Valid relationships: :data:`VALID_RELATIONSHIPS`
        """
        if not self.accession == source:
            raise RelationshipInvalidSourceError(logger=self.logger, source=source, sample_id=self.id)
        if not self.check_accession(target):
            raise RelationshipInvalidTargetError(logger=self.logger, target=target, sample_id=self.id)

        if 'relationships' not in self.entity:
            self.entity['relationships'] = []
        self.entity['relationships'].append({
            "source": source,
            "target": target,
            "type": relationship
        })

    @staticmethod
    def check_accession(accession) -> bool:
        """
        Check if the provided accession conforms to a BioSamples identifier. Pattern extracted from
        https://registry.identifiers.org/registry/biosample#!

        :param accession: Accession ID for the sample in BioSamples
        :return: True if correct format, False if not
        """
        return True if re.match('^SAM[NED](\\w)?\\d+$', accession) else False

    def _flatten_relationships(self, flattened_json: dict, relationships: list[dict]) -> dict:
        """
        Flatten relationships. To make it user friendly, limit it to Biosample --> target relationships. Biosamples
        defines both directionalities, but for flattening, this is way simpler and no information is lost.

        :param flattened_json: Flattened dictionary in progress.
        :param relationships: list of relationship dictionaries.

        :return: flattened dictionary with the processed relationships incorporated.
        """
        source_accession = self.accession
        relationship_types = set(VALID_RELATIONSHIPS)
        for relationship in relationships:
            if relationship['source'] != source_accession:
                continue
            if relationship['type'] not in flattened_json:
                flattened_json[relationship['type']] = []
            flattened_json[relationship['type']].append(relationship['target'])
        for relationship_type in relationship_types:
            flattened_json[relationship_type] = "||".join(flattened_json.get(relationship_type, []))
        return flattened_json

    def _flatten_characteristics(self, flattened_json: dict, characteristics: dict) -> dict:
        """
        flatten the characteristics.
        :param flattened_json: Flattened dictionary in progress.
        :param characteristics: dictionary with the characteristics.

        :return: flattened dictionary with the processed characteristics incorporated.
        """
        for field_name, values in characteristics.items():
            characteristic = values[0]
            for tag, value in characteristic.items():
                match tag:
                    case "text":
                        flattened_json[field_name] = value
                    case _:
                        # Returning units and ontologyTerm's to their natural habitat
                        flattened_json[f"{field_name}{self.delimiter}{tag}"] = value
            flattened_json[field_name] = "||".join([f"{v['text']}" for v in values])
        return flattened_json

    @staticmethod
    def _tag_is_valid(tag: str) -> bool:
        """
        Check if a tag is valid. Tags are evaluated against the :data:`VALID_TAGS` global. VALID_TAGS extracted from:
        https://www.ebi.ac.uk/biosamples/docs/references/api/submit#_sample

        :param tag: string with the tag name
        :return: True if valid, False if invalid
        """
        return tag in VALID_TAGS

    @staticmethod
    def guidelines() -> str:
        """
        Guidelines for filling out sample metadata for BioSamples.

        :return: Printable string with guidelines.
        """
        return BIOSAMPLES_GUIDELINES


BIOSAMPLES_GUIDELINES = "A Biosamples entity MUST have the following properties set:\n" \
                        "\t- name: a descriptive title for the sample\n" \
                        "\t- taxId or organism: either the integer code for a taxon ID (taxId), according to " \
                        "https://www.ncbi.nlm.nih.gov/taxonomy, or a string that validates against those records " \
                        "(organism)\nA Biosamples entity SHOULD have the following properties set:\n" \
                        "\t- release: date of release for the metadata of the entity. DEFAULTS TO MOMENT OF CREATION.\n" \
                        "For more information, please see " \
                        "https://www.ebi.ac.uk/biosamples/docs/references/api/submit#_submission_minimal_fields.\n\n" \
                        "To indicate relationships in the samples, please use a field named after the relationship" \
                        "itself: namely, 'derived_from', 'same_as', 'has_member' or 'child_of'.\nPlease see" \
                        "https://www.ebi.ac.uk/biosamples/docs/guides/relationships"