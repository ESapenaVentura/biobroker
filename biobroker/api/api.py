import datetime
import fnmatch
import multiprocessing
import os
import re
from platform import release

import requests
import io

from threading import Thread
from ftplib import FTP
from multiprocessing import Pool, Queue
from os.path import join
from uuid import uuid4
from json import JSONDecodeError


import pydantic_core

from requests.utils import requote_uri
from rich.progress import Progress, BarColumn, TimeRemainingColumn, TimeElapsedColumn, TextColumn
from progressbar import progressbar, AdaptiveETA, Percentage, FormatLabel, AnimatedMarker, Counter, ProgressBar

from biobroker.api.exceptions import CantBeUpdatedApiError, CantBeUpdatedLocalError, ChecklistValidationError, \
    BiosamplesValidationError, BiosamplesNoErrorMessageError, StructuredDataError, StructuredDataSubmissionError, \
    EnaNoSubmissionProvidedError, EnaAccessionTypeNotFound, EnaSubmissionError, AccessionsNotFound
from biobroker.metadata_entity import GenericEntity, Biosample, EnaEntity, EnaStudy, EnaProject, EnaSubmission, \
    EnaExperiment, EnaRun
from biobroker.metadata_entity.exceptions import EntityValidationError
from biobroker.authenticator import GenericAuthenticator, WebinAuthenticator
from biobroker.generic.exceptions import MandatoryFunctionNotSet
from biobroker.generic.logger import set_up_logger
from biobroker.generic.utilities import slice_list, get_file_details
from biobroker.generic.pydantic_model import StructuredDataModel, BiosampleGeneralEnaModel


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

    def submit(self, entities: list[type[GenericEntity]], **kwargs: dict) -> list[type[GenericEntity]]:
        """
        Generic function for submitting an iterable of entities to the archive.

        :param entities: list of GenericEntity subclasses.
        :param kwargs: Keyword arguments needed for subclasses for submitting.
        :return: list of GenericEntity subclasses after archival/deposition.
        """
        if not isinstance(entities, list):
            entities = [entities]
        if len(entities) > 1:
            return self._submit_multiple(entities, kwargs)
        else:
            return [self._submit(entities[0], kwargs)]

    def _submit(self, entity: type[GenericEntity], kwargs: dict) -> type[GenericEntity]:
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

    def retrieve(self, accession: str | list[str]) -> list[GenericEntity | None]:
        """
        Generic function for retrieving one or more entities accessing the API via a/some unique identifier/s
        (accession). Depending on the type of input parameter, calls :func:`~GenericApi._retrieve` or
        :func:`~GenericApi._retrieve_multiple`.

        :param accession: Unique identifier for the entity. Can be a string or a list of strings.

        :return: List of entities retrieved from the API. MUST always return a list for consistency.
        """
        if isinstance(accession, str):
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

    def update(self, entity: type[GenericEntity] | list[type[GenericEntity]]) -> list[GenericEntity]:
        """
        Update an entity. Should always take a list of entities as input, and each subclass decides how to handle
        the update.

        :param entity: List of GenericEntity's subclasses
        :return: List of updated GenericEntity's subclasses
        """
        if isinstance(entity, str):
            entity = [entity]
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

    def release(self, accession: list[str] | str) -> [GenericEntity]:
        """
        Release an entity to the public domain (or semi-public; saving myself future doc corrections)

        :param accession: Unique identifier for the entity.
        :return: The released entity, as it's in the archive.
        """
        if isinstance(accession, str):
            accession = [accession]
        if len(accession) > 1:
            return self._release_multiple(accession)
        return [self._release(accession[0])]

    def _release(self, accession: list[str]) -> GenericEntity:
        """
        Release an entity to the public domain (or semi-public; saving myself future doc corrections)

        :param accession: Unique identifier for the entity.
        :return: The released entity, as it's in the archive.
        """
        raise MandatoryFunctionNotSet(logger=self.logger)

    def _release_multiple(self, accession_list: list[str]) -> list[GenericEntity]:
        """
        Release multiple entities to the public domain (or semi-public; saving myself future doc corrections)

        :param accession_list: List of unique identifiers for the entities.
        :return: List of released entities, as they're in the archive.
        """
        raise MandatoryFunctionNotSet(logger=self.logger)

    def delete(self, accession: list[str] | str) -> None:
        """
        Delete an entity from the archive. This is a generic function, and subclasses should implement the specifics.
        """
        if isinstance(accession, str):
            accession = [accession]
        if len(accession) > 1:
            return self._delete_multiple(accession)
        return self._delete(accession[0])

    def _delete(self, accession: str) -> None:
        """
        Delete an entity from the archive. This is a generic function, and subclasses should implement the specifics.
        """
        raise MandatoryFunctionNotSet(logger=self.logger)

    def _delete_multiple(self, accession_list: list[str]) -> None:
        """
        Delete multiple entities from the archive. This is a generic function, and subclasses should implement the specifics.
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
        r = self.authenticator.post(submit_url, payload=entity)
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

    def _retrieve(self, accession: str) -> Biosample | None:
        """
        Retrieve a sample from BioSamples by using an accession

        :param accession: Accession ID, in BioSamples format
        :return: Biosample entity retrieved from the BioSample database
        """
        self.logger.info(f"Trying to retrieve sample with accession {accession}")
        try:
            return Biosample(self.authenticator.get(join(self.base_uri, accession)).json())
        except JSONDecodeError:
            self.logger.warning(f"Sample with accession {accession} not found.")
            return None

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

        is_invalid = self._is_invalid_for_update(entity)
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

    def _release(self, accesssion: list[str]):
        """
        Releases a single sample and makes it public.

        :param accesssion: Accession ID of the sample to be released
        """
        sample = self.retrieve(accesssion)[0]
        sample['release'] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        released_sample = self.update([sample])
        self.logger.info(f"Sample {accesssion}, with name {released_sample[0].id} released successfully.")
        return released_sample[0]

    def _release_multiple(self, accession_list: list[str]) -> list[GenericEntity]:
        """
        Releases multiple samples, making them public.

        :param accession_list: List of accessions to be released
        :return: List of released samples
        """
        return [self._release(accession) for accession in progressbar(accession_list,
                                                                      widgets=[FormatLabel('Releasing samples: '),
                                                                               Percentage(), " (", Counter(),
                                                                               f"/{len(accession_list)}) ",
                                                                               AnimatedMarker(markers='🀱🀲🀳🀴🀵🀶🀷🀾'
                                                                                                          '🁅🁌🁓🁚🁡'),
                                                                               " ", AdaptiveETA()])]

    def _delete(self, accession: str) -> None:
        """
        Delete a sample from the BioSamples database. This is a permanent action and cannot be undone. However,
        samples cannot be fully deleted in BSD, as they are persistent even when private. This function will just put
        an empty metadata dictionary in the sample and set it private for 100 years.
        """
        sample = self.retrieve(accession)[0]
        sample['characteristics'] = {}
        sample['organism'] = 'cellular organisms'
        sample['release'] = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365100)).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.update([sample])
        self.logger.info(f"Sample {accession} deleted successfully. Deleted attributes and made private for 100 years.")

    def _delete_multiple(self, accession_list: list[str]) -> None:
        """
        Delete multiple samples from the BioSamples database. This is a permanent action and cannot be undone. However,
        samples cannot be fully deleted in BSD, as they are persistent even when private. This function will just put
        an empty metadata dictionary in the sample and set it private for 100 years.
        """
        return [self._delete(accession) for accession in progressbar(accession_list,
                                                                      widgets=[FormatLabel('Deleting samples: '),
                                                                               Percentage(), " (", Counter(),
                                                                               f"/{len(accession_list)}) ",
                                                                               AnimatedMarker(markers='🀱🀲🀳🀴🀵🀶🀷🀾'
                                                                                                          '🁅🁌🁓🁚🁡'),
                                                                               " ", AdaptiveETA()])][0]

    # BioSamples-specific methods
    def validate_sample(self, entity: Biosample) -> requests.Response:
        """
        Validate a sample before submission. The errors returned are the same as the ones you get when you submit, so
        they are handled in the same way.

        :param entity: Biosample entity to be validated.
        :return: response, 200 if successful.
        """
        r = self.authenticator.post(url=self.validate_endpoint, payload=entity.entity)
        self._submit_errors(r)
        return r

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
        print(structured_data)
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
                raise BiosamplesNoErrorMessageError(response.status_code, response.text, self.logger)

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


class WebinV2Api(GenericApi):
    type_to_metadata_entity = {
        "studies": EnaStudy,
        "projects": EnaProject,
        "samples": Biosample,
        "experiments": EnaExperiment,
        "runs": EnaRun
    }
    ftp_uri = "webin2.ebi.ac.uk"
    """
    This is an API object specifically designed for ENA, to do submissions through the Webin API.

    Please note: If you need to access the 'dev' environment, pleese set up the environment variable 'API_ENVIRONMENT'
    with the value 'dev'. Otherwise, this API object will point to the production ENA and Webin-v2 API.

    :param authenticator: Subclass instance from the authenticator module. For Webin-v2, it's mandatory to set up a 
    WebinAuthenticator.
    :param verbose: True if logger should be set to INFO. Default WARNING.
    """
    def __init__(self, authenticator: WebinAuthenticator, verbose: bool = True):
        environment = 'dev' if 'dev' == os.environ.get('API_ENVIRONMENT', '') else ''
        base_uri = "https://www.ebi.ac.uk/ena/submit/webin-v2".replace('www', f"www{environment}")
        super().__init__(authenticator, base_uri, verbose)
        self.biosamples_api = authenticator
        self.logger.info(f"Set up Webin V2 API successfully: using base uri '{self.base_uri}'")

    @property
    def biosamples_api(self) -> BsdApi:
        return self._biosamples_api

    @biosamples_api.setter
    def biosamples_api(self, authenticator: WebinAuthenticator):
        self._biosamples_api = BsdApi(authenticator, verbose=False)

    @property
    def submit_endpoint(self) -> str:
        return join(self.base_uri, 'submit')

    def _submit_biosamples(self, entities: list[type[GenericEntity]]) -> tuple[list[Biosample], list[type[EnaEntity]]]:
        """
        This is a helper function to submit Biosamples to the BSD API. The main operations to perform are:
        1. Isolate the Biosample entities from the original array
        2. Validate them against the ENA default checklist mandatory fields (https://www.ebi.ac.uk/ena/browser/view/ERC000011)
        3. Submit them to BioSamples using the BSD API object.
        4. Return 2 lists: Submitted Biosamples and separated entities.

        The second step is very important, as it ensures that the samples are valid for submission to ENA. Biosamples is
        slightly less restrictive with the necessary fields, so this step is crucial, as samples could fail afterward.

        :param entities: All the entities to be submitted to ENA.
        :return: 2 lists: Submitted Biosamples and separated entities.
        """
        #1
        biosamples = [entity for entity in entities if isinstance(entity, Biosample)]
        self.logger.info("Validating Biosamples against the ENA checklist")
        errors = ""
        #2
        for sample in biosamples:
            try:
                sample.validate(BiosampleGeneralEnaModel)
            except EntityValidationError as e:
                errors += f"{e.message}\n"
        if errors:
            self.logger.error(errors)
            raise ValueError(f"Errors found in the Biosamples: \n{errors}\n\nPlease fix them before submitting again.")
        #3
        self.logger.info("Submitting Biosamples to BioSamples")
        biosamples = self.biosamples_api.submit(biosamples)
        #4
        return biosamples, [entity for entity in entities if not isinstance(entity, Biosample)]

    def _link_biosample_by_alias(self, submitted_samples: list[Biosample], entities: list[type[EnaEntity]]) -> list[type[EnaEntity]]:
        """
        Link submitted Biosamples with the EnaExperiment entities, using the alias of the Biosample as a linking property.
        This function is usually called during submission of full submissions to ENA.

        :param submitted_samples: List of submitted Biosamples
        :param entities: Rest of the entities submitted; EnaExperiment are extracted from this list.

        :return: List of entities with the Biosample alias linked to the accession. Biosample entities are not returned.
        """
        experiments = [entity for entity in entities if isinstance(entity, EnaExperiment)]
        alias_accession_map = {sample.id: sample['accession'] for sample in submitted_samples}
        for experiment in experiments:
            for sample in experiment['samples']:
                if not sample.get('accession'):
                    sample['accession'] = alias_accession_map.get(sample.get('alias'), None)
        return entities

    def _get_uploaded_files(self) -> list[str]:
        """
        Get a list of files present in the FTP area associated with the Webin account.
        """
        with FTP(self.ftp_uri, self.authenticator.username, self.authenticator.password) as ftp:
            files = ftp.nlst()
        return files

    def delete_file(self, file_name: str):
        """
        Delete a file in the FTP area associated with the Webin account.

        :param file_name: Name of the file to be deleted.

        :return: None
        """
        self.logger.info(f"Deleting file {file_name} from the Webin FTP server")
        if file_name not in self._get_uploaded_files():
            self.logger.warning(f"File {file_name} is not in the FTP server. Skipping deletion.")
            return
        with FTP(self.ftp_uri) as ftp:
            ftp.login(self.authenticator.username, self.authenticator.password)
            ftp.delete(file_name)
        self.logger.info(f"File {file_name} has been deleted")

    def delete_multiple_files(self, files: list[str]):
        """
        Delete multiple files in the FTP area associated with the Webin account.

        :param files: List of files to be deleted.

        :return: None
        """
        for file in files:
            self.delete_file(file)

    def _upload_progress_listener(self, queue: Queue, total_files: int):
        """
        Listener function for the upload progress. Runs in parallel with the upload threads to get updates from the
        queue and update the progress bar.

        :param queue: Queue object to get the progress updates. Shared amongst upload threads.
        :param total_files: Total number of files to be uploaded.

        :return: None
        """
        with Progress(
                TextColumn("[bold blue]{task.fields[filename]}"),
                BarColumn(),
                TextColumn("{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                TimeRemainingColumn()
        ) as progress:
            bars = {}  # Dictionary to store progress bars
            completed_files = 0  # Track number of finished files

            while completed_files < total_files:
                try:
                    file, progress_value = queue.get(timeout=1)
                    match progress_value:
                        case "DONE":
                            progress.update(bars[file], completed=100, refresh=True)
                            completed_files += 1
                        case "ERROR":
                            self.logger.error(f"Upload failed: {file}")
                            completed_files += 1
                        case _:
                            if file not in bars:
                                bars[file] = progress.add_task(file, total=100, filename=file)
                            progress.update(bars[file], completed=progress_value, refresh=True)
                except:
                    pass  # Avoid blocking

    def list_files(self, pattern: str="*") -> list[str]:
        """
        List files in the FTP area associated with the Webin account. Can filter by pattern.

        :param pattern: Pattern to filter the files. Default is all files (*).
        """
        all_files = self._get_uploaded_files()
        files_without_md5 = [file for file in all_files if not file.endswith(".md5")]
        return [file for file in files_without_md5 if fnmatch.fnmatch(file, pattern)]

    def upload_file(self, file_path: str, progress_bar_queue: Queue = None):
        """
        Upload a single file. If a Queue is passed, it is assumed that this function is being called in parallel and
        the listener function is being run in a thread, listening to the queue outputs.

        :param file_path: Path to the file to be uploaded.
        :param progress_bar_queue: Optional Queue object to get the progress updates. Shared amongst upload threads.
        """
        checksum, file_size = get_file_details(file_path)
        if progress_bar_queue is None:
            progress_bar_queue = Queue() # Create a queue if not provided, to ens
        uploaded = 0

        def callback(data):
            nonlocal uploaded
            uploaded += len(data)
            progress = min(100, int((uploaded / file_size) * 100))
            progress_bar_queue.put((file_path, progress))

        try:
            self.logger.info(f"Uploading file {file_path} to the Webin FTP server. MD5 will be calculated and uploaded.")
            with FTP(self.ftp_uri, self.authenticator.username, self.authenticator.password) as ftp:
                with open(file_path, 'rb') as f:
                    ftp.storbinary(f"STOR {file_path.split('/')[-1]}", f, callback=callback)
                    ftp.storbinary(f"STOR {file_path.split('/')[-1]}.md5", io.BytesIO(checksum.encode()))
            progress_bar_queue.put((file_path, "DONE"))
        except:
            self.delete_file(file_path.split('/')[-1])
            progress_bar_queue.put((file_path, "ERROR"))  # Mark as failed

    def _upload_run_files(self, runs: list[EnaRun]):
        """
        Upload the files associated with an ENA run, if they are not already uploaded. Multiple files will be uploaded
        at once.

        :param runs: List of EnaRun objects to upload the files from.
        """
        self.logger.info("Checking if files are already uploaded to the Webin FTP server")
        uploaded_files = self._get_uploaded_files()
        files_to_upload = []
        for run in runs:
            if run.submitted_files:
                continue
            for file in run.file_paths:
                filename = file.split('/')[-1]
                if filename not in uploaded_files:
                    files_to_upload.append(file)
        self.logger.info(f"Uploading {len(files_to_upload)} files. This may take a while.")
        with multiprocessing.get_context("spawn").Manager() as manager: # Manager to share the queue
            queue = manager.Queue()  # Queue for progress updates
            listener = Thread(target=self._upload_progress_listener, args=(queue, len(files_to_upload)), daemon=True)  # Listener process
            listener.start()
            with Pool(os.cpu_count() - 1) as pool:
                pool.starmap(self.upload_file, [(file, queue) for file in files_to_upload])
            listener.join()

    def _generate_submission_file(self, entities: type[EnaEntity] | Biosample, actions: list[dict] = None, release_date: str = None) -> dict:
        """
        Generate a submission file for Webin-v2. This file can be used both for submission and update, depending on
        the specified action.

        :param entities: List of EnaEntity subclasses to be updated.

        """
        if not actions:
            actions = [{'type': 'ADD'}]
        if release_date:
            actions.append({'type': 'HOLD', 'holdUntilDate': release_date})
        submission_file = {}
        for entity in entities:
            if not entity.submission_field_name in submission_file:
                submission_file[entity.submission_field_name] = []
            submission_file[entity.submission_field_name].append(entity)
        submission_file.update(
            {
                'submission': {
                    'actions': actions,
                    'alias': str(uuid4()),
                },

            }
        )
        self._check_submission_file(submission_file)
        return submission_file

    def _check_submission_file(self, submission_file: dict):
        """
        A bit of error fishing on the generated submission file. Errors that may be raised:

        - `~biobroker.api.exceptions.EnaNoSubmissionProvidedError`: No submission entity provided in the submission file.
        - Entities are not put in their respective place (e.g. ~biobroker.metadata_entity.EnaRun in 'runs' field)

        :param submission_file: Submission file to be checked.
        :return: None, if no errors are detected.

        """
        # 🐟
        if 'submission' not in submission_file:
            raise EnaNoSubmissionProvidedError(self.logger)

        for entity_type, entity_class in self.type_to_metadata_entity.items():
            if entity_type not in submission_file:
                continue
            assert all([isinstance(entity, entity_class) for entity in submission_file[entity_type]]), f"Invalid entity type in submission file: expected {entity_class}"
        self.logger.info("Submission file is valid.")

    def _check_receipt_success(self, receipt: dict):
        """
        Check the submission returns a successful receipt. If not, raise the errors.
        """
        if not receipt.get('success') and receipt.get('messages').get('error'):
            raise EnaSubmissionError(self.logger, receipt['messages'].get('error', []))

    def _receipt_to_entities(self, receipt: dict) -> list[type[EnaEntity]]:
        """
        Convert a submission receipt to a list of EnaEntity subclasses. This is used to return the entities that were
        submitted to ENA in a similar format, since ENA likes to return receipts.

        :param receipt: Receipt from the submission to ENA.
        :return: List of EnaEntity subclasses.
        """
        entities = []
        for entity_type, entity_class in self.type_to_metadata_entity.items():
            entities.extend([self.retrieve(entity['accession'])[0] for entity in receipt.get(entity_type, [])])
        return entities

    def _release_receipt_to_entities(self, receipt: dict) -> list[type[EnaEntity]]:
        """
        Convert a release receipt to a list of EnaEntity subclasses. This is used to return the entities that were
        released to ENA in a similar format, since ENA likes to return receipts.

        :param receipt: Receipt from the release to ENA.
        :return: List of EnaEntity subclasses.
        """
        entities = []
        for message in receipt.get('messages', {}).get('info', []):
            accession = message.split('"')[1]
            entities.extend(self.retrieve(accession))
        return entities

    def _submit(self, entity: type[EnaEntity | Biosample], kwargs: dict = None) -> list[type[EnaEntity] | Biosample]:
        """
        Submit a submission file to Webin-V2. Slightly different from the other submit functions, as Webin-V2 requires
        a submission file with at least one entity and a submission entity (To determine action), so in a normal scenario
        you would only submit multiple entities. This is kept for consistency, and in case you want to prepare the submission
        file yourself.

        :param entity: Submission file, as per stated .
        :param kwargs: Keyword argument. Accepted values are 'release_date'. If provided, the release date will be set.
        :return: a single, archived Biosample entity.
        """
        return self._submit_multiple([entity], kwargs)

    def _submit_multiple(self, entities: list[type[EnaEntity] | Biosample], kwargs: dict) -> list[type[EnaEntity] | Biosample]:
        """
        Submit a list of BioSample/ENA entities to BioSamples and ENA, using the webin-v2 submit endpoint.

        :param entities: Iterable (List/Tuple) of BioSample/EnaEntity objects. Must always be an iterable.
        :param kwargs: Keyword argument. No use for this function.

        :return: a list of BioSample/ENA entities
        """
        if not kwargs.get('release_date'):
            self.logger.info("No release date provided. Setting release date to 2 years from today.")
        release_date = kwargs.get('release_date', datetime.datetime.now() + datetime.timedelta(days=730)).strftime(
            "%Y-%m-%d")

        submitted_samples = []
        if any([isinstance(entity, EnaRun) for entity in entities]):
            runs = [entity for entity in entities if isinstance(entity, EnaRun)]
            self.logger.info("Runs have been detected. Checking for files; if they are not already uploaded, they will be"
                             " uploaded")
            self._upload_run_files(runs)
            self.logger.info("Run file upload operation completed")
        if any([isinstance(entity, Biosample) for entity in entities]):
            self.logger.info("Biosamples have been detected. Submitting them to BioSamples")
            submitted_samples, entities = self._submit_biosamples(entities)
            entities = self._link_biosample_by_alias(submitted_samples, entities)
            self.logger.info("Biosample submission operation completed. Linked to pertinent experiments")

        if entities:
            submission_file = self._generate_submission_file(entities, [{'type': 'ADD'}], release_date)
            self.logger.info("Submitting entities to Webin-V2")
            receipt = self.authenticator.post(self.submit_endpoint, payload=submission_file)
            receipt = receipt.json()
            self._check_receipt_success(receipt)
            self.logger.info(f"Submission successful. Submission accession: {receipt['submission']['accession']}")
            entities = self._receipt_to_entities(receipt)
        return entities + submitted_samples if submitted_samples else entities

    # Retrieve/update/delete/release functions

    def _retrieve(self, accession: str) -> type[EnaEntity] | Biosample | None:
        """
        Retrieve an entity from Webin. The type of entity will be determined by the accession provided.

        :param accession: Accession ID.
        :return: EnaEntity subclass or Biosample entity retrieved from the Webin or BSD API.
        """
        entity_type = self._assess_type_based_on_accession(accession)
        if entity_type == 'samples':
            return self.biosamples_api._retrieve(accession)
        endpoint = self._type_to_endpoint(entity_type)
        self.logger.info(f"Trying to retrieve {entity_type} with accession {accession}")
        retrieve_url = join(self.base_uri, endpoint)
        entity = self.authenticator.get(join(retrieve_url, accession))
        if entity.status_code == 404:
            self.logger.warning(f"Entity with accession {accession} not found.")
            return None

        return self.type_to_metadata_entity[entity_type]((self.authenticator.get(join(retrieve_url, accession)).json()))

    def _retrieve_multiple(self, accession_list: list[str]) -> list[Biosample]:
        """
        Retrieve multiple entities from Webin-V2 by providing a list of accessions.

        :param accession_list: Iterable (tuple|list) with accessions
        :return: List of BioSample entities retrieved from BioSamples API
        """
        entities = [self._retrieve(accession) for accession in progressbar(accession_list,
                                                                          widgets=[FormatLabel('Retrieving samples: '),
                                                                                   Percentage(), " (", Counter(),
                                                                                   f"/{len(accession_list)}) ",
                                                                                   AnimatedMarker(markers='🀱🀲🀳🀴🀵🀶🀷🀾'
                                                                                                          '🁅🁌🁓🁚🁡'),
                                                                                   " ", AdaptiveETA()])]
        return entities

    def _update(self, entity: type[EnaEntity] | Biosample) -> list[type[EnaEntity] | Biosample]:
        """
        Update a single entity. Since Webin-V2 requires receipts for updates, this function will call the
        `~biobroker.api.api._update_multiple` function to update the entity.

        :param entity: Biosample/EnaEntity subclass object loaded with the metadata, including the accession
        :return: Updated entity
        """
        return self._update_multiple([entity])

    def _update_multiple(self, entities: list[Biosample]) -> list[Biosample | type[EnaEntity]]:
        """
        Updates multiple entities in the ENA/BSD database. This function will check if the entity is a Biosample or
        an ENA entity, then update from Webin-v2 or Biosamples API using the `~biobroker.api.BsdApi.update` function.

        :param entities: List of Biosample/EnaEntity subclasses objects to update
        :return: List with updated Biosample/EnaEntity subclasses objects
        """
        no_accession_entities = list(filter(lambda x: not x.has_accession()))
        if no_accession_entities:
            raise AccessionsNotFound(no_accession_entities, self.logger)

        biosamples_entities = list(filter(lambda x: isinstance(x, Biosample), entities))
        ena_entities = list(filter(lambda x: not isinstance(x, Biosample), entities))

        if biosamples_entities:
            biosamples_entities = self.biosamples_api.update(biosamples_entities)
        if ena_entities:
            update_file = self._generate_submission_file(ena_entities, [{'type': 'MODIFY'}])
            ena_entities = self.authenticator.post(self.submit_endpoint, payload=update_file)


        return biosamples_entities + ena_entities

    def _delete(self, accession: list[str]) -> None:
        """
        Delete an entity from the ENA/BSD database.

        :param accession: Entity to be deleted.
        """
        if not isinstance(accession, list):
            accession = [accession]
        return self._delete_multiple(accession)

    def _release(self, accession: list[str]) -> list[type[GenericEntity]]:
        """
        Release an entity from the ENA/BSD database.

        :param accession: Entity to be released.
        """
        if not isinstance(accession, list):
            accession = [accession]
        return self._release_multiple(accession)

    def _release_multiple(self, accession_list: list[str]) -> list[type[GenericEntity]]:
        """
        Release a set of entities from the ENA/BSD database.

        :param accession_list: List of accessions to be released.
        :return: List of released samples.
        """
        accessions_ena = [accession for accession in accession_list if self._assess_type_based_on_accession(accession)
                          != 'samples']
        accessions_bsd = [accession for accession in accession_list if self._assess_type_based_on_accession(accession)
                          == 'samples']
        entities_ena = []
        entities_bsd = []
        if accessions_ena:
            actions = [{'type': 'RELEASE', 'target': accession} for accession in accessions_ena]
            submission_file = self._generate_submission_file([], actions)
            receipt = self.authenticator.post(self.submit_endpoint, payload=submission_file).json()
            self._check_receipt_success(receipt)
            entities_ena = self._release_receipt_to_entities(receipt)
        if accessions_bsd:
            entities_bsd = self.biosamples_api.release([accession for accession in accessions_bsd])
        entities = entities_ena + entities_bsd
        self.logger.info(f"Entities {','.join([entity.accession for entity in entities])} have been released "
                         "successfully.")
        return entities

    def _delete_multiple(self, accessions: list[str]) -> None:
        """
        Delete a set of entities from the ENA/BSD database.

        :param accessions: List of accessions to be deleted.
        :return: None
        """
        accessions_ena = [accession for accession in accessions if not self._assess_type_based_on_accession(accession)
                                                                       != 'samples']
        accessions_bsd = [accession for accession in accessions if not self._assess_type_based_on_accession(accession)
                                                                       == 'samples']
        if accessions_ena:
            actions = [{'type': 'CANCEL', 'target': accession} for accession in accessions_ena]
            submission_file = self._generate_submission_file([], actions)
            receipt = self.authenticator.post(self.submit_endpoint, payload=submission_file).json()
            self._check_receipt_success(receipt)
        if accessions_bsd:
            self.biosamples_api.delete(accessions_bsd)
        self.logger.info(f"Entities {','.join(accessions_ena + accessions_bsd)} have been deleted "
                         "successfully.")

    def _assess_type_based_on_accession(self, accession: str):
        """
        Assess the type of entity based on the accession provided.

        :param accession: Accession ID.
        """
        accession_regex = re.compile("^((?P<studies>[ES]RP\d+)|(?P<samples>([SE]RS|SAM(N|EA|D))\d+)|(?P<runs>[ES]RR\d+)|"
                                     "(?P<projects>PRJ(EB|NA)\d+)|(?P<experiments>[ES]RX\d+)|(?P<analysis>[ES]RZ\d+))$")
        matched_accession = accession_regex.match(accession)
        if not matched_accession:
            raise EnaAccessionTypeNotFound(self.logger, accession)
        matched_accession_by_type = matched_accession.groupdict()
        return next(key for key, value in matched_accession_by_type.items() if value)

    @staticmethod
    def _type_to_endpoint(entity_type: str) -> str:
        """
        I love consistency within the same archives. This is just a super necessary, not at all redundant method
        because they couldn't call an endpoint the same way as in the JSON file that you use to submit. Fun!

        :param entity_type: Type of entity to get the endpoint for.
        :return: Endpoint for the entity type.
        """
        return {
            "studies": "study",
            "projects": "project",
            "samples": "sample",
            "experiments": "experiment",
            "runs": "run"
        }.get(entity_type, "")