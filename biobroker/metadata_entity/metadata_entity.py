import json
import re
from glob import glob

import pydantic_core
from typing import Any, Type

from pydantic import BaseModel

from biobroker.generic.pydantic_model import EnaExperimentModel, EnaSubmissionModel, \
    EnaProjectModel, EnaStudyModel, EnaRunModel, BiosampleGeneralModel

from biobroker.metadata_entity.exceptions import (RelationshipInvalidSourceError, RelationshipInvalidTargetError,
                                                  EntityValidationError, FileNumberDoesNotMatchError)
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
    :patam data_model: BaseModel subclass determining the metadata model to validate the `metadata_content`.
    """
    def __init__(self, metadata_content: dict, data_model: type[BaseModel], verbose: bool = False):
        self.logger = set_up_logger(self, verbose=verbose)
        self._entity = None
        self.entity = metadata_content
        self.validate(data_model=data_model)

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

    def validate(self, data_model: Type[BaseModel]):
        """
        Validate the metadata content using a Pydantic data model. Each subclass can define its own data model, or it
        can be provided by the user on validation.
        """
        try:
            self.entity = json.loads(data_model(**self.entity).model_dump_json(exclude_unset=True, by_alias=True))
        except pydantic_core.ValidationError as pydantic_error:
            raise EntityValidationError(self.logger, entity_id=self.id, errors=pydantic_error.errors()) from None


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

    def has_accession(self) -> bool:
        """
        Check if the entity has an accession.

        :return: True if the entity has an accession, False if not.
        """
        return self.accession != ""

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


class Biosample(GenericEntity):
    """
    Biosamples metadata entity. Contains the necessary information to process a non-nested JSON into a valid Biosamples
    sample.

    Current known issue: Only setting up and expecting one value for the properties inside characteristics. Well, this
    is because... Biosamples also expects that! No clue why properties are defaulting to arrays.

    :param metadata_content: non-nested dictionary containing the metadata for the sample.
    :param data_model: Optional parameter, used to evaluate the metadata content. Defaults to :cls:`~biobroker.generic.pydantic_model.BiosampleGeneralModel`
    :param delimiter: optional parameter, used for key delimiters. Used mainly to manage attributes tags, such as
                      'unit' and 'ontologyTerms'. Explained further in
                      :func:`~broker.metadata_entity.biosample.Biosample.__setitem__`, point 4.
    :param verbose: True if logger should be set to INFO. Default WARNING.
    """
    ROOT_PROPERTIES = ['name', 'release', 'relationships', 'accession', 'sraAccession', 'webinSubmissionAccountId',
                       'status', 'update', 'characteristics', 'submittedVia', 'create', '_links', 'submitted', 'taxId',
                       'structuredData', 'externalReferences', 'organization']
    VALID_TAGS = ['text', 'ontologyTerms', 'unit', 'tag']
    VALID_RELATIONSHIPS = ["derived_from", "same_as"]
    EXTERNAL_REFERENCE_FIELD = "url"
    ORGANIZATION = "organizationName"
    def __init__(self, metadata_content: dict, data_model: Type[BaseModel] = BiosampleGeneralModel,
                 delimiter: str = "||", verbose: bool = False):
        self.delimiter = delimiter
        super().__init__(metadata_content, data_model=data_model, verbose=verbose)

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
        self._entity = {"characteristics": {}}
        for field, value in metadata.items():
            if value is None:
                continue
            self[field] = value

    def flatten(self) -> dict:
        """
        Flatten the :attr:`~Biosample.entity` property and return a non-nested dictionary. This will be mostly used for
        output generation.

        :return: flattened dictionary
        """
        sample_json = self.to_json()
        flattened_json = {}
        for key, value in sample_json.items():
            match key:
                case 'relationships':
                    # Relationships are flattened using just the relationship type. Keep it user-friendly!
                    flattened_json = self._flatten_relationships(flattened_json, value)
                case 'characteristics':
                    flattened_json = self._flatten_characteristics(flattened_json, sample_json[key])
                case '_links':
                    # No need to flatten the _links. _links are not useful in output generation.
                    pass
                case 'externalReferences':
                    flattened_json = self._flatten_urls(flattened_json, sample_json[key])
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
        You can delete tags by using delimiter e.g. temperature||unit

        :param key: Key to search for for deletion
        :return:
        """
        if key in Biosample.ROOT_PROPERTIES:
            del self.entity[key]
        else:
            keys = key.split(self.delimiter)
            match len(keys):
                case 1:
                    del self.entity['characteristics'][keys[0]]
                case 2:
                    del self.entity['characteristics'][keys[0]][0][keys[1]]
                case _:
                    # In Biosamples, nesting is limited to 1 level
                    raise KeyError(key)

    def __setitem__(self, key: str, value: Any):
        """
        This is a special method to set up values to "entity" in a dict-like manner. Each entity can decide to implement
        checks (Depending on the archive needs) or just return "self.entity[key] = value".

        Tags for the attributes can be set up from the flattened input dictionary. As such, each sample has
        a delimiter set up, and if it's detected, instead of replacing the value, it will add the tag (e.g.
        `{'size': 1, 'size||unit': 'cm'}` will be translated to `{'size': [{'text': 1, 'unit': cm}]}`). Please see
        https://www.ebi.ac.uk/biosamples/docs/references/api/submit#_sample for more information.

        :param key: name of the attribute.
        :param value: value of the attribute.
        """

        # Root values
        if key in Biosample.ROOT_PROPERTIES:
            self.entity[key] = value
        # Relationships
        elif self.accession and key in Biosample.VALID_RELATIONSHIPS and all([
            self.check_accession(accession) for accession in value.split(self.delimiter)]):
            for target in value.split(self.delimiter):
                self.add_relationship(source=self.accession,
                                      target=target,
                                      relationship=key)
        # External references
        elif key == Biosample.EXTERNAL_REFERENCE_FIELD:
            for url in value.split(self.delimiter):
                self.add_external_reference(url=url)
        # Organizations - Since there is no documentation I will assume it only has a name
        elif key == Biosample.ORGANIZATION:
            for organization in value.split(self.delimiter):
                self.add_organization(organization=organization)
        # characteristics
        else:
            characteristic = self.entity.get('characteristics').get(key, [{}])[0]
            # Managing the elements of the attributes in characteristics. Check
            # https://www.ebi.ac.uk/biosamples/docs/references/api/submit#_sample
            if self.delimiter in key:
                key, tag_name = key.split(self.delimiter)
                if not self._tag_is_valid(tag_name):
                    self.logger.warning(f"Tag '{tag_name}' on property '{key}' is not a documented valid tag. "
                                        "It may be rejected on submission.")
                characteristic = self.entity['characteristics'].get(key, [{}])[0]
                # Kinda hate to have soooo many ifs, but every field has its own rules...
                characteristic[tag_name] = value if tag_name != 'ontologyTerms' else value.split(self.delimiter)
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

    def add_relationship(self, source, target, relationship):
        """
        Add a relationship to the entity. Source must be the entity's accession; target must be a valid BioSamples
        accession; relationship must be a valid relationship.

        :param source: source entity accession (Must be equal to entity)
        :param target: target sample accession
        :param relationship: Relationship between source and target. Valid relationships: :attr:`~Biosample.VALID_RELATIONSHIPS`
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

    def add_external_reference(self, url: str):
        """
        Add an external reference to the entity.

        :param url: URL to the external reference
        """
        if 'externalReferences' not in self.entity:
            self.entity['externalReferences'] = []
        self.entity['externalReferences'].append({'url': url})

    def add_organization(self, organization):
        if 'organization' not in self.entity:
            self.entity['organization'] = []
        self.entity['organization'].append({'Name': organization})

    def _flatten_relationships(self, flattened_json: dict, relationships: list[dict]) -> dict:
        """
        Flatten relationships. To make it user friendly, limit it to Biosample --> target relationships. Biosamples
        defines both directionalities, but for flattening, this is way simpler and no information is lost.

        :param flattened_json: Flattened dictionary in progress.
        :param relationships: list of relationship dictionaries.

        :return: flattened dictionary with the processed relationships incorporated.
        """
        source_accession = self.accession
        relationship_types = set(Biosample.VALID_RELATIONSHIPS)
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
                    case 'unit':
                        # Returning units and ontologyTerm's to their natural habitat
                        flattened_json[f"{field_name}{self.delimiter}{tag}"] = value
                    case 'ontologyTerms':
                        flattened_json[f"{field_name}{self.delimiter}{tag}"] = self.delimiter.join(value)
                    case _:
                        self.logger.warning(f'Sample {self.id}: tag {tag} not recognised. Not flattening its value: {value}')
            flattened_json[field_name] = "||".join([f"{v['text']}" for v in values])
        return flattened_json

    def _flatten_urls(self, flattened_json: dict, urls: dict):
        """
        Flatten the externalReferences.

        :param flattened_json: Flattened dictionary in progress.
        :param urls: dictionary with the urls.

        :return: flattened dictionary with the processed urls incorporated.

        """
        flattened_json['url'] = self.delimiter.join([value['url'] for value in urls])
        return flattened_json

    @staticmethod
    def check_accession(accession) -> bool:
        """
        Check if the provided accession conforms to a BioSamples identifier. Pattern extracted from
        https://registry.identifiers.org/registry/biosample#!

        :param accession: Accession ID for the sample in BioSamples
        :return: True if correct format, False if not
        """
        return True if re.match('^SAM[NED](\\w)?\\d+$', accession) else False

    @staticmethod
    def _tag_is_valid(tag: str) -> bool:
        """
        Check if a tag is valid. Tags are evaluated against the :attr:`~Biosample.VALID_TAGS` global. VALID_TAGS extracted from:
        https://www.ebi.ac.uk/biosamples/docs/references/api/submit#_sample

        :param tag: string with the tag name
        :return: True if valid, False if invalid
        """
        return tag in Biosample.VALID_TAGS

    @staticmethod
    def guidelines() -> str:
        """
        Guidelines for filling out sample metadata for BioSamples.

        :return: Printable string with guidelines.
        """
        return BIOSAMPLES_GUIDELINES


BIOSAMPLES_GUIDELINES = "A Biosamples entity MUST have the following properties set:\n" \
                        "\t- name: a descriptive title for the sample\n" \
                        "\t- organism: a string that validates against NCBITaxon records \n" \
                        "\t- release: date of release for the metadata of the entity, in YYYY-MM-DD format. Accepts iso format\n" \
                        "For more information, please see " \
                        "https://www.ebi.ac.uk/biosamples/docs/references/api/submit#_submission_minimal_fields.\n\n" \
                        "To indicate relationships in the samples, please use a field named after the relationship" \
                        "itself: namely, 'derived_from', 'same_as', 'has_member' or 'child_of'.\nPlease see" \
                        "https://www.ebi.ac.uk/biosamples/docs/guides/relationships"

class EnaEntity(GenericEntity):
    """
    ENA submission metadata entity. Contains the necessary information to process a non-nested JSON into a valid ENA
    submission containing all the other necessary entities.

    :param metadata_content: non-nested dictionary containing the metadata for the sample.
    :param data_model: Optional parameter, used to evaluate the metadata content. Defaults to :cls:`~biobroker.generic.pydantic_model.BiosampleGeneralModel`
    :param delimiter: optional parameter, used for key delimiters. Used mainly to manage attributes tags, such as
                          'unit' and 'ontologyTerms'. Explained further in
                          :func:`~broker.metadata_entity.biosample.Biosample.__setitem__`, point 4.
    :param verbose: True if logger should be set to INFO. Default WARNING.
    """
    submission_field_name = None
    ROOT_PROPERTIES = ["alias", "accession", "identifiers", "centerName", "title", "instrumentPlatform",
                       "instrumentModel", "study", "samples", "libraryDescriptor", "experiment", "files",
                       "attributes", "actions"]

    def __init__(self, metadata_content: dict, data_model: type[BaseModel], delimiter: str="||", verbose: bool=False):
        self.delimiter = delimiter
        super().__init__(metadata_content, data_model=data_model, verbose=verbose)

    @property
    def complex_fields(self):
        """
        Return the property 'complex_fields'. Must be overriden by subclasses. Lists all the properties that
        are complex (nested).

        :raises: `~biobroker.generic.exceptions.MandatoryFunctionNotSet`
        """
        raise MandatoryFunctionNotSet(self.logger)

    @property
    def complex_fields_array(self):
        """
        Return the property 'complex_fields'. Must be overriden by subclasses. Lists all the properties that
        are complex (nested) and an array.

        :raises: `~biobroker.generic.exceptions.MandatoryFunctionNotSet`
        """
        raise MandatoryFunctionNotSet(self.logger)

    @property
    def id(self):
        """
        Return the property 'id', extracting it from the 'name' property. Defaults to an empty string.

        :return:
        """
        return self.entity.get('alias', '')

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
        self._entity = {}
        for field, value in metadata.items():
            if value is None:
                continue
            self[field] = value

    def __getitem__(self, item) -> str | int | dict | list:
        """
        Special method to get values from the EnaEntity.entity. Tries to obtain it from root and then complex fields;
        raises ValueError if not found.

        :param item: Value of the key to look up for

        :return: Value of the item if found.
        """
        if self.delimiter in item:
            item = item.split(self.delimiter)
            if item[0] in self.complex_fields:
                return self.entity[item[0]][item[1]]
            elif item[0] in self.complex_fields_array:
                return [complex_field[item[1]] for complex_field in self.entity[item[0]]]
            else:
                return [attribute[item[1]] for attribute in self.entity[item[0]]]
        return self.entity[item]

    def __delitem__(self, key: str):
        """
        Special method to delete the values from an EnaEntity.entity subclass.
        You can delete tags of non-array fields by using delimiter, e.g. libraryDescriptor||libraryName

        :param key: Key to search for for deletion
        :return:
        """

        if key in EnaEntity.ROOT_PROPERTIES:
            del self.entity[key]
        elif key in self.complex_fields:
            keys = key.split(self.delimiter)
            match len(keys):
                case 1:
                    del self.entity[keys[0]]
                case 2:
                    del self.entity[keys[0]][0][keys[1]]
                case _:
                    # Nested values maximum nesting level
                    raise KeyError(key)
        else:
            del self.entity['attributes'][key]

    def __setitem__(self, key: str, value: Any):
        """
        Special method to set the items for the EnaEntity subclasses, either in the root as-is, as complex fields
        (Array or single field, usually used for linking), or as attributes (Anything else)

        :param key: name of the attribute.
        :param value: value of the attribute.
        """
        if key in EnaEntity.ROOT_PROPERTIES:
            self.entity[key] = value

        elif key.split(self.delimiter)[0] in self.complex_fields or key.split(self.delimiter)[0] in self.complex_fields_array:
            key, tag = key.split(self.delimiter)
            values = value.split(self.delimiter)
            self._add_complex_fields(key, tag, values)
        else:
            if not self.entity.get('attributes'):
                self.entity['attributes'] = []
            if not key in self.entity['attributes']:
                self.entity['attributes'].append({'tag': key, "value": value, "unit": None})
            return

    def __contains__(self, item: str) -> bool:
        """
        Special method to check if EnaEntity.entity  contains 'item'.
        :param item: value of the key to check for.
        :return: True if found, False if not found.
        """
        return item in self.entity or item in (value['tag'] for value in self.entity.get('attributes', []))


    def _add_complex_fields(self, key: str, tag: str, values: list):
        """
        Add a complex field, either as an array or as a

        """
        if key not in self.entity:
            self.entity[key] = [{} for _ in range(len(values))]
            if key in self.complex_fields:
                self.entity[key] = self.entity[key][0]
        if key in self.complex_fields:
            # For non-array fields, need to re-convert
            self.entity[key][tag] = values[0]
        else:
            for i, value in enumerate(values):
                self.entity[key][i][tag] = value

    def _flatten_complex_fields(self, flattened_json, key, value):
        for tag, field_value in value.items():
            flattened_json[f"{key}{self.delimiter}{tag}"] = field_value
        return flattened_json

    def _flatten_complex_array_fields(self, flattened_json, key, value):
        for array_element in value:
            empty_dict = dict()
            flattened_complex_field = self._flatten_complex_fields(empty_dict, key, array_element)
            for tag, field_value in flattened_complex_field.items():
                if not tag in flattened_json:
                    flattened_json[tag] = field_value
                else:
                    flattened_json[tag] += f"{self.delimiter}{field_value}"
        return flattened_json


    def _flatten_attributes(self, flattened_json, value):
        for attribute in value:
            flattened_json[attribute['tag']] = attribute['value']
        return flattened_json

    def flatten(self) -> dict:
        """
        Flatten the :attr:`~EnaEntity.entity` property and return a non-nested dictionary. This will be mostly used for
        output generation.

        :return: flattened dictionary
        """
        sample_json = self.to_json()
        flattened_json = {}
        for key, value in sample_json.items():
            if key in self.complex_fields:
                flattened_json = self._flatten_complex_fields(flattened_json, key, value)
            elif key in self.complex_fields_array:
                flattened_json = self._flatten_complex_array_fields(flattened_json, key, value)
            elif key == 'attributes':
                flattened_json = self._flatten_attributes(flattened_json, value)
            else:
                flattened_json[key] = value
        return flattened_json

    @staticmethod
    def guidelines() -> str:
        """
        Guidelines for filling out sample metadata for BioSamples.

        :return: Printable string with guidelines.
        """
        return ENA_GUIDELINES

ENA_GUIDELINES = ("A submission to ENA is composed of multiple elements:\n"
                  "\t- EnaSubmission: An object containing the information about the data packet, such as the release "
                  "date and what to do with the rest of the objects (Create new entries, modify existing, etc). This "
                  "is the only necessary entity."
                  "\n\t- EnaRun: An object that contains information about the data files."
                  "\n\t- EnaExperiment: An object that contains information about multiple runs and the library preparation"
                  "\n\t- EnaStudy: An object that contains information about the group of experiments"
                  "\n\t- EnaProject: An object that contains information about a group of studies"
                  "For more information, please see https://ena-docs.readthedocs.io/en/latest/submit/general-guide/metadata.html.")

class EnaExperiment(EnaEntity):
    submission_field_name = "experiments"
    """
    ENA experiment entity. This is a subclass to an `~biobroker.metadata_entity.metadata_entity.EnaEntity`;
    it's a very simple subclass for the purpose of defining specific traits to the "Experiment" entities in ENA.
    Everything else inherits from `~biobroker.metadata_entity.metadata_entity.EnaEntity`

    :param metadata_content: Metadata content of the ENA experiment
    :param data_model: Data model to validate the ENA experiment. Defaults to `~biobroker.generic.pydantic_model.EnaExperimentModel`
    :param delimiter: optional parameter, used for key delimiters. Used mainly to manage complex fields.
    :param verbose: True if logger should be set to INFO. Default WARNING.
    """
    def __init__(self, metadata_content: dict, data_model: type[BaseModel] = EnaExperimentModel, delimiter: str = "||",
                 verbose: bool = False):
        super().__init__(metadata_content, data_model=data_model, delimiter=delimiter, verbose=verbose)

    @property
    def complex_fields(self):
        return ['libraryDescriptor', 'study']

    @property
    def complex_fields_array(self):
        return ['samples']

class EnaRun(EnaEntity):
    submission_field_name = "runs"
    """
    ENA run entity. This is a subclass to an `~biobroker.metadata_entity.metadata_entity.EnaEntity`;
    it's a very simple subclass for the purpose of defining specific traits to the "Experiment" entities in ENA.
    Everything else inherits from `~biobroker.metadata_entity.metadata_entity.EnaEntity`

    :param metadata_content: Metadata content of the ENA experiment
    :param data_model: Data model to validate the ENA experiment. Defaults to `~biobroker.generic.pydantic_model.EnaExperimentModel`
    :param delimiter: optional parameter, used for key delimiters. Used mainly to manage complex fields.
    :param verbose: True if logger should be set to INFO. Default WARNING.
    """

    def __init__(self, metadata_content: dict, data_model: type[BaseModel] = EnaRunModel, delimiter: str = "||",
                 verbose: bool = False, file_path_folder: str = ".", recursive_file_search: bool = True):
        if 'filePath' in metadata_content:
            file_path_folder = metadata_content['filePath']
            del metadata_content['filePath']
        super().__init__(metadata_content, data_model=data_model, delimiter=delimiter, verbose=verbose)
        self.file_path_folder = file_path_folder
        self.recursive_file_search = recursive_file_search
        self.submitted_files = False
        self.file_paths = self._check_files()

    @property
    def complex_fields(self):
        """
        List of complex fields. A complex field is just a nested dictionary. Overrides parent property.
        """
        return ['experiment']

    @property
    def complex_fields_array(self):
        """
        List of complex fields that are contained within arrays. A complex field is just a nested dictionary, but needs
        special treatment when it is expected in the form of an array. Overrides parent property.
        """
        return ['samples', 'files']

    def _check_files(self):
        """
        Check that the filenames provided correspond to existing files. If recursive_file_search is set to true in the
        instance, this search happens recursively. This information is returned to be used for data upload.

        :return: list of file paths
        """
        filenames = [f['fileName'] for f in self['files']]
        if all([re.match("run/ERR\d{3}/ERR\d+/.+", filename) for filename in filenames]):
            self.submitted_files = True
            return [file.split('/')[-1] for file in filenames]
        file_paths = [file_path for filename in filenames for file_path in
                      glob(f"{self.file_path_folder}/**/{filename}", recursive=self.recursive_file_search)]
        if len(file_paths) != len(filenames):
            raise FileNumberDoesNotMatchError(self.logger, filenames, file_paths)
        return file_paths


class EnaStudy(EnaEntity):
    submission_field_name = "studies"
    """
    ENA study entity. This is a subclass to an `~biobroker.metadata_entity.metadata_entity.EnaEntity`;
    it's a very simple subclass for the purpose of defining specific traits to the "Study" entities in ENA.
    Everything else inherits from `~biobroker.metadata_entity.metadata_entity.EnaEntity`

    :param metadata_content: Metadata content of the ENA experiment
    :param data_model: Data model to validate the ENA experiment. Defaults to `~biobroker.generic.pydantic_model.EnaExperimentModel`
    :param delimiter: optional parameter, used for key delimiters. Used mainly to manage complex fields.
    :param verbose: True if logger should be set to INFO. Default WARNING.
    """
    def __init__(self, metadata_content: dict, data_model: type[BaseModel] = EnaStudyModel, delimiter: str = "||",
                 verbose: bool = False):
        super().__init__(metadata_content, data_model=data_model, delimiter=delimiter, verbose=verbose)

    @property
    def complex_fields(self):
        return []

    @property
    def complex_fields_array(self):
        return []


class EnaProject(EnaEntity):
    submission_field_name = "projects"
    """
    ENA project entity. This is a subclass to an `~biobroker.metadata_entity.metadata_entity.EnaEntity`;
    it's a very simple subclass for the purpose of defining specific traits to the "Project" entities in ENA.
    Everything else inherits from `~biobroker.metadata_entity.metadata_entity.EnaEntity`

    :param metadata_content: Metadata content of the ENA experiment
    :param data_model: Data model to validate the ENA experiment. Defaults to `~biobroker.generic.pydantic_model.EnaExperimentModel`
    :param delimiter: optional parameter, used for key delimiters. Used mainly to manage complex fields.
    :param verbose: True if logger should be set to INFO. Default WARNING.
    """
    def __init__(self, metadata_content: dict, data_model: type[BaseModel] = EnaProjectModel, delimiter: str = "||",
                 verbose: bool = False):
        super().__init__(metadata_content, data_model=data_model, delimiter=delimiter, verbose=verbose)

    @property
    def complex_fields(self):
        return []

    @property
    def complex_fields_array(self):
        return []

class EnaSubmission(EnaEntity):
    submission_field_name = 'submission'
    """
    ENA submission entity. This is a subclass to an `~biobroker.metadata_entity.metadata_entity.EnaEntity`;
    it's a very simple subclass for the purpose of defining specific traits to the "Submission" entities in ENA.
    Everything else inherits from `~biobroker.metadata_entity.metadata_entity.EnaEntity`

    :param metadata_content: Metadata content of the ENA experiment
    :param data_model: Data model to validate the ENA experiment. Defaults to `~biobroker.generic.pydantic_model.EnaExperimentModel`
    :param delimiter: optional parameter, used for key delimiters. Used mainly to manage complex fields.
    :param verbose: True if logger should be set to INFO. Default WARNING.
    """
    def __init__(self, metadata_content: dict, data_model: type[BaseModel] = EnaSubmissionModel,
                 delimiter: str = "||", verbose: bool = False):
        super().__init__(metadata_content, data_model=data_model, delimiter=delimiter, verbose=verbose)

    @property
    def complex_fields(self):
        return []

    @property
    def complex_fields_array(self):
        return ["actions"]