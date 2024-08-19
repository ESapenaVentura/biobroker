from typing import Type

from biobroker.api import GenericApi
from biobroker.authenticator import GenericAuthenticator
from biobroker.input_processor import GenericInputProcessor
from biobroker.metadata_entity import GenericEntity
from biobroker.output_processor import GenericOutputProcessor

from biobroker.generic.logger import set_up_logger


class Wrangler:
    """
    Wrapper submodule! Provides with the very basic functionality expected for all subclasses of all the generic
    submodules defined in the library. Currently allows:

    - Submitting a set of entities to an archive
    - Retrieving a set of entities from an archive
    - Saving a set of entities to a file

    And the functionality depends on what submodule you create it with!

    :param api: Subclass of :mod:`broker.api.generic_api.GenericApi`
    :param authenticator: Subclass of :mod:`broker.authenticator.generic_authenticator.GenericAuthenticator`
    :param input_processor: Subclass of :mod:`broker.input_processor.generic_input_processor.GenericInputProcessor`
    :param entity: Subclass of :mod:`broker.metadata_entity.generic_entity.GenericEntity` (Please notice, you need to
                   pass a class to this parameter)
    :param output_processor: subclass of :mod:`broker.output_processor.generic_output_processor.GenericOutputProcessor`
    """
    def __init__(self, api: GenericApi, authenticator: GenericAuthenticator, input_processor: GenericInputProcessor,
                 entity: Type[GenericEntity], output_processor: GenericOutputProcessor):
        self.logger = set_up_logger(instance_object=self, verbose=True)
        self.authenticator = authenticator
        self.input_processor = input_processor
        self.api = api
        self.output_processor = output_processor
        self.entities = self.input_processor.process(entity=entity)

    def submit(self, entities: list[GenericEntity]) -> list[GenericEntity]:
        """
        Submit the entities to the archive.

        :param entities: List of genericEntity's.

        :return: List of entities submitted
        """
        return self.api.submit(entities)

    def save_results(self, entities):
        """
        Save the entities to a file.

        :param entities: Entities to be saved to a file
        """
        self.output_processor.save(entities)

    def retrieve_entities(self, accession_list: list[str]) -> list[GenericEntity]:
        """
        Retrieve entities by using an accession

        :param accession_list: list of strings containing the accessions.
        :return:
        """
        return self.api.retrieve(accession_list)

