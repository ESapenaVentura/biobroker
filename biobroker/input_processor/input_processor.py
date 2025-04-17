from copy import deepcopy
from typing import Type

from pandas import read_csv, read_excel
from numpy import nan

from biobroker.generic.exceptions import MandatoryFunctionNotSet
from biobroker.generic.logger import set_up_logger
from biobroker.input_processor.exceptions import (CantProcessBothEntityTypes, CantProcessNoEntityTypes,
                                                  InputDataIsComplexError, TooManyEntitiesSpecifiedError)
from biobroker.metadata_entity import GenericEntity

"""
Test the behave tests
"""

class GenericInputProcessor:
    """
    Generic input processor.

    :param input_data_path: Path to the input file.
    :param verbose: Boolean indicating if the logger should be verbose.
    """
    def __init__(self, input_data_path: str, verbose: bool = False):
        self._input_data = ''
        self.logger = set_up_logger(self, verbose=verbose)
        self.input_data = input_data_path

    @property
    def input_data(self) -> list[dict] | dict[str, list[dict]]:
        """
        Input data in JSON format. Set from input_path by setter

        :return: Input data in JSON format
        """
        return self._input_data

    @input_data.setter
    def input_data(self, path: str) -> list[dict] | dict[str, list[dict]]:
        """
        SUBCLASSES MUST OVERRIDE THIS PROPERTY.

        Must assign "self._input_data" input for the "process" function to use.
        """
        raise MandatoryFunctionNotSet(self.logger)

    def _check_entity_length_matches_input_data(self, entities_map: dict[str, Type[GenericEntity]]):
        """
        Check if the length of the entity dictionary matches the length of the input data. There are three main outcomes:
        - Length is equal (0): Continue processing
        - Length is lesser (-1): This means that there are more entities specified than there are to process. Raise error.
        - Length is greater (1): This means that there are more types of input data than specified entities. Warn user.

        :param entities_map: Entity map provided to `~biobroker.input_processor.GenericInputProcessor.process`.
        """
        match (len(entities_map) > len(self.input_data)) - (len(entities_map) < len(self.input_data)):
            case 1:
                raise TooManyEntitiesSpecifiedError(self.logger, list(entities_map.keys()))
            case -1:
                self.logger.warning(f"There are more entities in the input data than specified in the entities_map. "
                                    f"These entities won't be processed: "
                                    f"{','.join(set(self.input_data.keys()) - set(entities_map.keys()))}")

    def process(self, entity: Type[GenericEntity] = None, entities_map: dict[str, Type[GenericEntity]] = None) -> list[Type[GenericEntity]]:
        """
        Process self.input_data and return a list of metadata entities that depend on the 'GenericEntity' subclass
        passed to the function.

        Any field with value "None" should be processed by the entity type; different services may require different
        behaviours.

        :param entity: GenericEntity subclass (Not instance) to process the input data into.
        :param entities_map: Dictionary of {name_of_sheet: GenericEntity subclass} to return a complex list.
        :return: list of entities. Must be a subclass of GenericEntity
        """
        if entity and entities_map:
            raise CantProcessBothEntityTypes(self.logger)
        if not entity and not entities_map:
            raise CantProcessNoEntityTypes(self.logger)
        entities = []
        if entity:
            entities_map = {"": entity}
            if isinstance(self.input_data, dict):
                raise InputDataIsComplexError(self.logger, list(self.input_data.keys()))
        else:
            self._check_entity_length_matches_input_data(entities_map)
        entity_creation_errors = False
        for key, entity in entities_map.items():
            input_data = self.input_data if not key else self.input_data[key]
            for json_entity in input_data:
                try:
                    new_entity = entity(metadata_content=deepcopy(json_entity))
                except:
                    entity_creation_errors = True
                    continue
                entities.append(new_entity)
        if entity_creation_errors:
            self.logger.error("There were errors processing the entities. Please check the logs for more information."
                              "No entities will be returned until all the input data is correct.")
            return []
        return entities

    def transform(self, field_mapping: dict, delete_non_mapped_fields: bool = False):
        """
        Transform the input data retrieved from the source to have new keys based on an {<old_key>: <new_key>} map. Only
        simple key name change operations are allowed.

        :param field_mapping: {'old_key': 'new_key'} dictionary. Not nested.
        :param delete_non_mapped_fields: Boolean to indicate if fields not present in the map above should be deleted.
               Defaults False
        """
        for i, entity in enumerate(self.input_data):
            for key, value in field_mapping.items():
                try:
                    field_value = entity.pop(key)
                except KeyError:
                    self.logger.warning(f"'transform' function: Key {key} was not found in entity with index {i}. "
                                        "This entity will not be updated")
                    break
                entity[value] = field_value
            if delete_non_mapped_fields:
                [entity.pop(key) for key in entity.keys() if key not in field_mapping.keys()]


class TsvInputProcessor(GenericInputProcessor):
    """
    TSV input processor. Loads a TSV file with entity metadata.

    :param input_data: Path to the file with the input metadata
    :param field_mapping: Path to the file with the field mapping
    """
    def __init__(self, input_data):
        super().__init__(input_data)

    @GenericInputProcessor.input_data.setter
    def input_data(self, path: str):
        """
        Setter for input_data property. Reads a TSV file with the pandas library, and returns a list with JSON files.

        :param path: Path to input data
        """
        file = read_csv(path, sep="\t", encoding='cp437').fillna(nan).replace([nan], [None])
        json_file = file.to_dict(orient='records')
        self._input_data = json_file


class XlsxInputProcessor(GenericInputProcessor):
    """
    XLSX input processor. Loads a XLSX file with entity metadata.

    :param input_data: Path to the file with the input metadata.
    :param worksheet_name: Name of the worksheet to be processed.
    """
    def __init__(self, input_data: str, sheet_name: str = "Sheet1"):
        self.sheet_name = sheet_name
        super().__init__(input_data)

    @GenericInputProcessor.input_data.setter
    def input_data(self, path):
        """
        Setter for the input_data property. Reads an xlsx file, on a specific worksheet name.

        :param path: Path to the file with the input metadata.
        """
        with open(path, 'rb') as f:
            file = read_excel(f, engine='openpyxl', sheet_name=self.sheet_name).fillna(nan).replace([nan], [None])
        json_file = file.to_dict(orient='records')
        self._input_data = json_file

class ComplexXlsxInputProcessor(GenericInputProcessor):
    """
    XLSX complex input processor. Loads a XLSX file with entity metadata split across several tabs.

    :param input_data: Path to the file with the input metadata.
    :param worksheet_name: Names of the worksheets to be processed.
    """
    def __init__(self, input_data: str, sheet_names: list[str] | None =None):
        if sheet_names is None:
            sheet_names = ["Sheet1"]
        self.sheet_names = sheet_names
        super().__init__(input_data)

    @GenericInputProcessor.input_data.setter
    def input_data(self, path):
        json_file = {}
        for sheet_name in self.sheet_names:
            with open(path, 'rb') as f:
                tab = read_excel(f, engine='openpyxl', sheet_name=sheet_name).fillna(nan).replace([nan], [None])
            json_file[sheet_name] = tab.to_dict(orient='records')
        self._input_data = json_file