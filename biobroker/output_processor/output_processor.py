import pandas

from biobroker.generic.exceptions import MandatoryFunctionNotSet
from biobroker.generic.logger import set_up_logger
from biobroker.metadata_entity import GenericEntity


class GenericOutputProcessor:
    """
    Generic output processor. Defines the mandatory functions for the subclasses to function.

    :param output_path: path to save the file. Please include the name and extension of the file.
    """
    def __init__(self, output_path: str, verbose: bool = False):
        self.logger = set_up_logger(self, verbose=verbose)
        self.path = output_path

    def save(self, entities: list[GenericEntity]):
        """
        Transform the entities into a dataframe to use pandas functionality to save.

        :param entities: Subclasses of GenericEntity.
        """
        entity_by_type = {entity_class.__name__: list(filter(lambda x: isinstance(x, entity_class), entities))
                          for entity_class in set(entity.__class__ for entity in entities)}
        dataframes = {entity_type: pandas.DataFrame([entity.flatten() for entity in entities]) for entity_type, entities in
                                          entity_by_type.items()}
        self._save(dataframes)

    def _save(self, dataframe: dict[str, pandas.DataFrame]):
        """
        Function to be overriden by subclasses. Takes a dataframe and saves the output into self.path.

        :param dataframe: Dataframe containing the flattened metadata from the GenericEntity subclasses.
        """
        raise MandatoryFunctionNotSet(logger=self.logger)


class TsvOutputProcessor(GenericOutputProcessor):
    """
    TSV output processor. Takes a list of entities and outputs a TSV with the metadata processed.

    :param output_path: Path to the file being saved. Please include tsv extension.
    """
    def __init__(self, output_path: str):
        super().__init__(output_path)

    def _save(self, dataframe: dict[str, pandas.DataFrame]):
        """
        Save the resulting dataframe from :func:`~GenericOutputProcessor.save` into a tsv,
        using pandas functionality. NO, the delimiter is not customizable. Create another subclass if you want that.
        TSV means `TAB-Separated Values`, not comma, not pipes, not anything else. You weirdo.

        :param dataframe: Dataframe containing the flattened metadata from the GenericEntity subclasses.
        """
        separator = '\t'
        if len(dataframe) > 1:
            self.logger.warning("More than one entity type found in the output data. All entities will be crammed into "
                                "a single TSV file. This may cause issues with the output data columns.")
        dataframe = pandas.concat(dataframe.values(), ignore_index=True)
        dataframe.to_csv(self.path, sep=separator, index=False)


class XlsxOutputProcessor(GenericOutputProcessor):
    """
    Excel output processor. Takes a list of entities and outputs an excel file with the metadata processed.

    :param output_path: Path to the file being saved. Please include '.xlsx' extension.
    """
    def __init__(self, output_path, sheet_name: str = 'Sheet1'):
        super().__init__(output_path)
        self.sheet_name = sheet_name

    def _save(self, dataframe: dict[str, pandas.DataFrame]):
        """
        Save the resulting dataframe from :func:`~GenericOutputProcessor.save` into an Excel file.

        :param dataframe: Dataframe containing the flattened metadata from the GenericEntity subclasses.
        """
        if len(dataframe) > 1:
            self.logger.warning("More than one entity type found in the output data. All entities will be crammed into "
                                "a single Excel file. This may cause issues with the output data columns.")
        dataframe = pandas.concat(dataframe.values(), ignore_index=True)
        dataframe.to_excel(self.path, index=False, sheet_name=self.sheet_name, engine='openpyxl')

class ComplexXlsxOutputProcessor(GenericOutputProcessor):
    """
    Excel output processor for complex metadata. Takes a list of entities and outputs an excel file with the metadata
    processed.

    :param output_path: Path to the file being saved. Please include '.xlsx' extension.
    """
    def __init__(self, output_path, sheet_names: dict[str, str] = None):
        super().__init__(output_path)
        self.sheet_names = sheet_names if sheet_names else {}
        self._check_sheet_names()

    def _save(self, dataframe: dict[str, pandas.DataFrame]):
        """
        Save the resulting dataframe from :func:`~GenericOutputProcessor.save` into an excel.

        :param dataframe: Dataframe containing the flattened metadata from the GenericEntity subclasses.
        """
        with pandas.ExcelWriter(self.path, engine='openpyxl') as writer:
            for class_name, entities in dataframe.items():
                if class_name not in self.sheet_names:
                    self.logger.warning(f"Entity of type {class_name} not found in sheet names. "
                                        f"Sheet will be created with default class naming ('{class_name}').")
                    self.sheet_names[class_name] = class_name
                entities.to_excel(writer, index=False, sheet_name=self.sheet_names[class_name], engine='openpyxl')

    def _check_sheet_names(self):
        """
        Check the sheet names. Pandas/Python errors are not straight-forward for users.
        """
        if not isinstance(self.sheet_names, dict):
            raise TypeError("sheet_names attribute must be a dictionary or left empty.")


