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
        json_to_save = [entity.flatten() for entity in entities]
        dataframe = pandas.DataFrame(json_to_save)
        self._save(dataframe)

    def _save(self, dataframe: pandas.DataFrame):
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

    def _save(self, dataframe: pandas.DataFrame):
        """
        Save the resulting dataframe from :func:`~GenericOutputProcessor.save` into a tsv,
        using pandas functionality. NO, the delimiter is not customizable. Create another subclass if you want that.
        TSV means `TAB-Separated Values`, not comma, not pipes, not anything else. You weirdo.

        :param dataframe: Dataframe containing the flattened metadata from the GenericEntity subclasses.
        """
        separator = '\t'
        dataframe.to_csv(self.path, sep=separator, index=False)


class XlsxOutputProcessor(GenericOutputProcessor):
    """
    Excel output processor. Takes a list of entities and outputs an excel file with the metadata processed.

    :param output_path: Path to the file being saved. Please include '.xlsx' extension.
    """
    def __init__(self, output_path, sheet_name: str = 'Sheet1'):
        super().__init__(output_path)
        self.sheet_name = sheet_name

    def _save(self, dataframe: pandas.DataFrame):
        """
        Save the resulting dataframe from :func:`~GenericOutputProcessor.save` into an excel.

        :param dataframe: Dataframe containing the flattened metadata from the GenericEntity subclasses.
        """
        dataframe.to_excel(self.path, index=False, sheet_name=self.sheet_name, engine='openpyxl')
