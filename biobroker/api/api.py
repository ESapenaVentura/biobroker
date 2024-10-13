import os

import requests

from os.path import join
from requests.utils import requote_uri

from progressbar import progressbar, AdaptiveETA, Percentage, FormatLabel, AnimatedMarker, Counter, ProgressBar

from biobroker.api.exceptions import CantBeUpdatedApiError, CantBeUpdatedLocalError, ChecklistValidationError, \
    BiosamplesValidationError, BiosamplesNoErrorMessageError, StructuredDataError, StructuredDataSubmissionError
from biobroker.metadata_entity import Biosample
from biobroker.metadata_entity import GenericEntity
from biobroker.authenticator import GenericAuthenticator
from biobroker.generic.exceptions import MandatoryFunctionNotSet
from biobroker.generic.logger import set_up_logger
from biobroker.generic.utilities import slice_list
from biobroker.generic.pydantic_model import StructuredDataModel

import pydantic_core


## TODO: BsdApi Build self url. Self points to general biosamples...


class GenericApi:
    """
    Generic API class. This class defines the minimal functions and class properties needed for the rest of the API
    classes.

    :param authenticator: Authenticator object. Requests are handled through the authenticator.
    :param base_uri: Base (root) uri of the API.
    :param verbose: Boolean indicating if the logger should be verbose.
    """
    def __init__(self, authenticator: GenericAuthenticator, base_uri: str, verbose: bool = True):
        self.authenticator = authenticator
        self.base_uri = base_uri
        self.logger = set_up_logger(self, verbose)

    def submit(self, entities: list[GenericEntity], **kwargs: dict) -> list[GenericEntity]:
        """
        Generic function for submitting an iterable of entities to the archive.

        :param entities: list of GenericEntity subclasses.
        :param kwargs: Keyword arguments needed for subclasses for submitting.
        :return: list of GenericEntity subclasses after archival/deposition.
        """
        if len(entities) > 1:
            return self._submit_multiple(entities, kwargs)
        else:
            return [self._submit(entities[0], kwargs)]

    def _submit(self, entity: GenericEntity, kwargs: dict) -> GenericEntity:
        """
        Generic function for submitting an entity to an archive.

        :param entity: Subclass of GenericEntity
        :param kwargs: Keyword arguments needed for subclasses' method.
        :return: Submitted GenericEntity subclass
        """
        raise MandatoryFunctionNotSet(self.logger)

    def _submit_multiple(self, entities: list[GenericEntity], kwargs: dict) -> list[GenericEntity]:
        """
        Generic function for submitting multiple entities to an archive.

        :param entities: List of subclasses of GenericEntity
        :param kwargs: Keyword arguments needed for subclasses' method.
        :return: Submitted GenericEntity subclasses
        """
        raise MandatoryFunctionNotSet(self.logger)

    def retrieve(self, accession: list[str]) -> list[GenericEntity]:
        """
        Generic function for retrieving one or more entities accessing the API via a/some unique identifier/s
        (accession). Depending on the type of input parameter, calls :func:`~GenericApi._retrieve` or
        :func:`~GenericApi._retrieve_multiple`.

        :param accession: Unique identifier for the entity. Can be a string or a list of strings.

        :return: List of entities retrieved from the API. MUST always return a list for consistency.
        """
        if not isinstance(accession, list):
            accession = [accession]
        if len(accession) > 1:
            return self._retrieve_multiple(accession)
        return [self._retrieve(accession[0])]

    def _retrieve(self, accession: str) -> GenericEntity:
        """
        Retrieve one entity via a unique identifier (accession).

        :param accession: Unique identifier for the entity.
        :return: An entity retrieved from the API.
        """
        raise MandatoryFunctionNotSet(logger=self.logger)

    def _retrieve_multiple(self, accession_list) -> list[GenericEntity]:
        """
        Retrieve multiple entities via a list of unique identifiers (accessions).

        :param accession_list: List of unique identifiers for the entities to retrieve.

        :return: List of entities.
        """
        raise MandatoryFunctionNotSet(logger=self.logger)

    def update(self, entity: list[GenericEntity]) -> list[GenericEntity]:
        """
        Update an entity. Should always take a list of entities as input, and each subclass decides how to handle
        the update.

        :param entity: List of GenericEntity's subclasses
        :return: List of updated GenericEntity's subclasses
        """
        if len(entity) > 1:
            return self._update_multiple(entity)
        return [self._update(entity[0])]

    def _update(self, entity: GenericEntity) -> GenericEntity:
        """
        Update an entity via the API.

        :param entity: GenericEntity subclass, corresponding to an entry in the database.
        :return: An updated GenericEntity subclass
        """
        raise MandatoryFunctionNotSet(logger=self.logger)

    def _update_multiple(self, entities: list[GenericEntity]) -> list[GenericEntity]:
        """
        Update multiple entities via the API.

        :param entities: list of GenericEntity subclasses, corresponding to several entries in the database.
        :return: list of updated GenericEntity's subclasses
        """
        raise MandatoryFunctionNotSet(logger=self.logger)


class BsdApi(GenericApi):
    """
    This is an API object specifically designed for the BioSamples Database.

    Please note: If you need to access the 'dev' environment, pleese set up the environment variable 'API_ENVIRONMENT'
    with the value 'dev'. Otherwise, this API object will point to the production BioSamples archive.

    :param authenticator: Subclass instance from the authenticator module. For BioSamples, it's recommended to use
                          the WebinAuthenticator.
    :param verbose: True if logger should be set to INFO. Default WARNING.
    """
    def __init__(self, authenticator: GenericAuthenticator, verbose: bool = True):
        environment = 'dev' if 'dev' == os.environ.get('API_ENVIRONMENT', '') else ''
        base_uri = "https://www.ebi.ac.uk/biosamples/samples".replace('www', f"www{environment}")
        super().__init__(authenticator, base_uri, verbose)
        self.bulk_accession_endpoint = join(self.base_uri.replace("biosamples/", "biosamples/v2/"), 'bulk-accession')
        self.bulk_submit_endpoint = join(self.base_uri.replace("biosamples/", "biosamples/v2/"), 'bulk-submit')
        self.validate_endpoint = join(self.base_uri, 'validate')
        self.structured_data_endpoint = self.base_uri.replace('/samples', '/structureddata')
        self.logger.info(f"Set up BSD API successfully: using base uri '{self.base_uri}'")
        self.relationship_types = ["derived_from", "same_as"]

    def _submit(self, entity: Biosample, kwargs: dict) -> Biosample:
        """
        Submit a single Biosample entity to BSD.

        :param entity: Biosample GenericEntity subclass.
        :param kwargs: Keyword argument. No use for this function.
        :return: a single, archived Biosample entity.
        """
        submit_url = self.base_uri
        r = self.authenticator.post(submit_url, payload=entity.entity)
        if r.status_code > 300:
            self._submit_errors(r)
        return Biosample(r.json())

    def _submit_multiple(self, entities: list[Biosample], kwargs: dict) -> list[Biosample]:
        """
        Submit a list of BioSample entities to biosamples, using the bulk-submit endpoint.

        :param entities: Iterable (List/Tuple) of BioSample objects. Must always be an iterable.
        :param kwargs: Keyword argument:

                       - 'chunk_size': integer, may be set up to determine the size of chunks to send to BSD at
                         once. Due to BSD technical limitations, capped at 500.
                       - 'process_relationships': bool, if set to true, after submission, updates the samples with
                         the relationships.

        :return: a list of BioSample entities
        """
        submission_results = []
        chunk_size = min(kwargs.get('chunk_size', 500), 500)
        self.logger.info(f"Submitting {len(entities)} samples to bulk endpoint: {self.bulk_submit_endpoint}")
        for entity_chunk in slice_list(entities, chunk_size):
            r = self.authenticator.post(self.bulk_submit_endpoint,
                                        payload=entity_chunk)
            if r.status_code > 300:
                self._submit_errors(r)
            results = r.json()
            submission_results.extend([Biosample(result) for result in results])

        if kwargs.get('process_relationships'):
            self.logger.info("Processing sample relationships. This may take a while.")
            submission_results = self.process_relationships(entities=submission_results)
        return submission_results

    # Retrieve/update/delete functions

    def _retrieve(self, accession: str) -> Biosample:
        """
        Retrieve a sample from BioSamples by using an accession

        :param accession: Accession ID, in BioSamples format
        :return: Biosample entity retrieved from the BioSample database
        """
        self.logger.info(f"Trying to retrieve sample with accession {accession}")
        return Biosample(self.authenticator.get(join(self.base_uri, accession)).json())

    def _retrieve_multiple(self, accession_list: list[str]) -> list[Biosample]:
        """
        Retrieve multiple samples from BioSamples by providing a list of accessions.

        :param accession_list: Iterable (tuple|list) with accessions
        :return: List of BioSample entities retrieved from BioSamples API
        """
        samples = [self._retrieve(accession) for accession in progressbar(accession_list,
                                                                          widgets=[FormatLabel('Retrieving samples: '),
                                                                                   Percentage(), " (", Counter(),
                                                                                   f"/{len(accession_list)}) ",
                                                                                   AnimatedMarker(markers='🀱🀲🀳🀴🀵🀶🀷🀾'
                                                                                                          '🁅🁌🁓🁚🁡'),
                                                                                   " ", AdaptiveETA()])]
        return samples

    def _update(self, entity: Biosample) -> Biosample:
        """
        Update a sample that is already in the BioSamples database. Samples must be updated using the FULL metadata, as
        per BSD specifications https://www.ebi.ac.uk/biosamples/docs/references/api/submit#_update_sample

        :param entity: Biosample object loaded with the metadata, including the accession
        :return: Updated sample contained in Biosample object
        """

        is_invalid = BsdApi._is_invalid_for_update(entity)
        if is_invalid:
            raise CantBeUpdatedLocalError(sample_id=entity.id, reasons=is_invalid, logger=self.logger)
        sample_url = os.path.join(self.base_uri, entity.accession)
        response = self.authenticator.put(url=sample_url, payload=entity.entity)
        if response.status_code > 300:
            raise CantBeUpdatedApiError(sample_id=entity.id, response=response, logger=self.logger)
        return Biosample(response.json())

    def _update_multiple(self, entities: list[Biosample]) -> list[Biosample]:
        """
        Updates multiple samples in the BSD database. Since they can only be updated once at a time, calls
        :func:`~Biosample._update` once per sample in list.

        :param entities: List of Biosample entities to update
        :return: List with updated Biosample entities
        """
        return [self._update(entity) for entity in progressbar(entities,
                                                               widgets=[FormatLabel('Updating samples: '),
                                                                        Percentage(), " (", Counter(),
                                                                        f"/{len(entities)}) ",
                                                                        AnimatedMarker(markers='🀱🀲🀳🀴🀵🀶🀷🀾🁅🁌🁓🁚🁡'), " ",
                                                                        AdaptiveETA()])]

    # BioSamples-specific

    def validate_sample(self, entity: Biosample):
        """
        Validate a sample before submission. The errors returned are the same as the ones you get when you submit, so
        they are handled in the same way.

        :param entity: Biosample entity to be validated.
        :return:
        """
        r = self.authenticator.post(url=self.validate_endpoint, payload=entity.entity)
        self._submit_errors(r)

    def process_relationships(self, entities: list[Biosample]) -> list[Biosample]:
        """
        Process the relationships from a list of submitted entities. Assumes the relationships are defined in the
        metadata as `characteristics.derived_from/same_as`, and that the entities are linked via their `name`,
        not accession.

        If multiple relationships of the same type have to be defined, please use the :attr:`~biobroker.metadata_entity.Biosample.delimiter`
        as the input value (e.g. same_sample1||same_sample2 under `same_as` property)

        :param entities: List of Biosample entities to update their relationships.
        :return: list of updated entities
        """
        id_to_accession = {entity.id: entity.accession for entity in entities}
        for entity in entities:
            for relationship_type in self.relationship_types:
                if relationship_type in entity:
                    for split_relationship_value in entity[relationship_type]['text'].split(entity.delimiter):
                        target = split_relationship_value if Biosample.check_accession(split_relationship_value) \
                            else id_to_accession[split_relationship_value]
                        entity.add_relationship(source=entity.accession,
                                                target=target,
                                                relationship=relationship_type)
                    del entity[relationship_type]
        updated_entities = self.update(entities)
        return updated_entities

    def search_samples(self, text: str = "", attributes=None) -> list[Biosample]:
        """
        Search for samples in the Biosamples database. Can either search using free text (Can be improved using the
        query syntax specified here: https://www.ebi.ac.uk/ebisearch/documentation) or by attributes' values. For the
        attributes, please provide them as a dictionary.

        :param text: free text for the search. Can use query syntax for search engines (AND/OR etc)
        :param attributes: Attributes to filter by. Has to be provided as a dictionary {<attribute_name>: <attr. value>}
        :return: list of Biosamples or an empty list.
        """
        if attributes is None:
            attributes = dict()
        search_query = self._build_search_query(text, attributes)
        query_url = f"{self.base_uri}?{search_query}"

        response = self.authenticator.get(query_url).json()
        len_sample_search = response['page']['totalElements']
        size = response['page']['size']
        if not response.get('_embedded'):
            return []
        samples = response['_embedded']['samples']

        progress_bar = ProgressBar(widgets=[FormatLabel('Retrieving samples: '),
                                            Percentage(), " (", Counter(),
                                            f"/{len_sample_search}) ",
                                            AnimatedMarker(markers='🀱🀲🀳🀴🀵🀶🀷🀾🁅🁌🁓🁚🁡'), " ",
                                            AdaptiveETA()], max_value=len_sample_search)

        current = size
        while response['_links'].get('next'):
            response = self.authenticator.get(response['_links']['next']['href']).json()
            samples.extend(response['_embedded']['samples'])
            progress_bar.update(current)
            current += size
        progress_bar.finish()

        return [Biosample(sample) for sample in samples]

    def submit_structured_data(self, structured_data: dict) -> list[Biosample]:
        """
        Submit structured data to a sample in BioSamples. The data is checked before submission. May raise:
        - :exc:`~biobroker.api.exceptions.StructuredDataError`: Pre-submission errors
        - :exc:`~biobroker.api.exceptions.StructuredDataSubmissionError`: Post-submission errors

        :param structured_data: Structured data that's going to be posted in BSD. Must follow the format in https://www.ebi.ac.uk/biosamples/docs/references/api/submit#_submit_structured_data
        :return: Biosample entity with the structured data
        """
        self._check_structured_data(structured_data=structured_data)
        structured_data_put_uri = join(self.structured_data_endpoint, structured_data['accession'])
        response = self.authenticator.put(url=structured_data_put_uri, payload=structured_data)
        if response.status_code == 200:
            return self.retrieve([structured_data['accession']])
        raise StructuredDataSubmissionError(self.logger, response)


    def _check_structured_data(self, structured_data: dict):
        """
        Check the structured data is correct using the data models and pydantic.
        Model used: :cls:`~biobroker.metadata_entity.data_model.StructuredDataModel`

        :param structured_data: Structured data.
        :raises: :exc:`~biobroker.api.exceptions.StructuredDataError`
        """
        try:
            StructuredDataModel.model_validate(structured_data)
        except pydantic_core.ValidationError as pydantic_error:
            raise StructuredDataError(logger=self.logger, errors=pydantic_error.errors())

    def _submit_errors(self, response: requests.Response) -> None:
        """
        Submission errors and how they should be handled. Biosamples returns non-jsonable responses sometimes so this
        handles the type and display of errors during submission.

        Errors being raised:
            - :exc:`~biobroker.api.exceptions.ChecklistValidationError` : Checklist validation has failed
            - :exc:`~biobroker.api.exceptions.BiosamplesValidationError` : BSD minimal sample checklist error. Returned differently, because why not

        :param response: response obtained during submission. Usually r.status_code > 300
        :return: None if no errors are detected.
        """
        if "Checklist validation failed" in response.text:
            raise ChecklistValidationError(response.text, self.logger)

        if response.status_code == 400:
            if "dataPath" in response.text:
                raise BiosamplesValidationError(response.text, self.logger)
            else:
                raise BiosamplesNoErrorMessageError(response.status_code, self.logger)

        return None

    @staticmethod
    def _build_search_query(text: str, attributes: dict) -> str:
        """
        Build the search query for BSD. Attributes need to be joined. Page=0 is specified to return pagination in the
        BioSamples API (Non-documented behaviour)

        :param text: Free text to search by.
        :param attributes: Dictionary of attributes and values to filter by.
        :return:
        """
        attributes_str = "&".join([f"filter=attr:{key}:{value}" for key, value in attributes.items()])
        query = f"text={text}&{attributes_str}&page=0"
        return requote_uri(query)

    @staticmethod
    def _is_invalid_for_update(entity: Biosample) -> list[str] | bool:
        """
        Checks if the sample is invalid for update.

        :param entity: Sample to be checked.
        :return: A list of validation errors or false
        """
        conditions = {
            "Accession not set in metadata": entity.accession,
            "Invalid accession format": entity.check_accession(entity.accession)
        }
        checks = [condition for condition, check in conditions.items() if not check]
        return checks if checks else False
