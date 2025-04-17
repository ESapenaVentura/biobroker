import logging
import json
from requests import Response

from json.decoder import JSONDecodeError

from biobroker.generic.utilities import parse_pydantic_errors


def parse_checklist_validation_errors(validation_errors: list[dict]):
    """
    Parse a checklist validation error and return it in a printable state.

    :param validation_errors: Response list with validation error dictionaries, containing `dataPath` and `errors`.
    :return: printable string.
    """
    validation_errors_str = "\n\t- ".join([f"{validation_errors[i]['dataPath'].replace('/characteristics/', '')}: "
                                           f"{','.join(validation_errors[i]['errors'])}"
                                           for i in range(len(validation_errors))])
    return validation_errors_str

class AccessionsNotFound(Exception):
    def __init__(self, entity_id: list[str], logger: logging.Logger):
        """
        Raise when accession is not found.

        :param accession: string passed as an accession
        :param logger: subclass logger to log the error message to.
        """
        message = f"Could not find accession in entity '{','.join(entity_id)}'"
        logger.error(message)
        super().__init__(message)

class AccessionHasIncorrectFormat(Exception):
    def __init__(self, accession: str, logger: logging.Logger):
        """
        Raise when accession has incorrect format.

        :param accession: string passed as an accession
        :param logger: subclasss logger to log the error message to.
        """
        message = f"Could not retrieve accession {accession}; Incorrect format"
        logger.error(message)
        super().__init__(message)


class CantBeUpdatedApiError(Exception):
    def __init__(self, sample_id, response: Response, logger: logging.Logger):
        """
        Raise when an error comes from an API update request.

        :param sample_id: Id of the sample that raised the error
        :param response: errored response (r.status_code >= 300)
        :param logger: subclasss logger to log the error message to.
        """
        try:
            message = f"Sample with ID {sample_id} can't be updated:\n\t-Error type: {response.json()['error']}" \
                      f"\n\t-Error message: {response.json()['message']}"
        except TypeError:
            # Can't be updated, but response does not contain "error" dataPath
            message = f"Sample with ID {sample_id} can't be updated:\n\t- {parse_checklist_validation_errors(response.json())}"
        except JSONDecodeError:
            # Validation against checklist failed, returns a non-jsonable message
            validation_errors = json.loads(response.text.split('failed: ')[2])
            validation_errors_str = parse_checklist_validation_errors(validation_errors)
            message = f"Sample with ID {sample_id} failed update due to checklist errors:\n\t- {validation_errors_str}"
        logger.error(message)
        super().__init__(message)


class CantBeUpdatedLocalError(Exception):
    def __init__(self, sample_id: str, reasons: list[str], logger: logging.Logger):
        """
        Raise when an error comes from an update request, before doing the request.

        :param sample_id: ID of the sample that fail validation.
        :param reasons: list of reasons (strings) as to why validation failed.
        :param logger: subclass logger to log the error message to.
        """
        reasons_str = "\n\t- ".join(reasons)
        self.message = f"Sample with ID {sample_id} can't be updated - Error(s): \n\t- {reasons_str}"
        logger.error(self.message)
        super().__init__(self.message)


class BiosamplesValidationError(Exception):
    def __init__(self, response_text: str, logger: logging.Logger):
        """
        Raise a Biosamples minimal checklist validation error
        (https://www.ebi.ac.uk/biosamples/schemas/certification/biosamples-minimal.json)

        :param response_text: text from the response.
        :param logger: subclass logger to log the error message to.
        """
        validation_errors = json.loads(response_text)
        errors_str = parse_checklist_validation_errors(validation_errors)
        self.message = f"Found following errors in sample validation:\n\t- {errors_str})"
        logger.error(self.message)
        super().__init__(self.message)


class BiosamplesNoErrorMessageError(Exception):
    def __init__(self, status_code: int, response_text: str, logger: logging.Logger):
        """
        Raise an error without any other issue but a 400 in the response and no text whatsoever.
        Current testing (Completely empirical) has told me that this can be raised in the following situations:
            - `release` in incorrect format

        :param logger: subclass logger to log the error message to.
        """
        self.message = (f"It's dangerous to go alone, take this error code: '{status_code}' with you (There was no "
                        f"error message). If this helps, the response text was: '{response_text}'")
        logger.error(self.message)
        super().__init__(self.message)


# I know this is repeated in the update error, but BSD does not return the sample ID with the creation of the sample.
# TODO: Future possible update: raise this error from cantbeupdated, with optional sample parameter. Right now not needed.
class ChecklistValidationError(Exception):
    def __init__(self, response_text: str, logger: logging.Logger):
        """
        Raise a checklist validation error.

        :param response_text: Text of the response.
        :param logger: subclass logger to log the error message to.
        """
        # Validation against checklist failed, returns a non-jsonable message
        validation_errors = json.loads(response_text.split('failed: ')[2])
        validation_errors_str = parse_checklist_validation_errors(validation_errors)
        self.message = f"Samples failed checklist validation with the following errors: \n\t- {validation_errors_str}"
        logger.error(self.message)
        super().__init__(self.message)


class StructuredDataError(Exception):
    def __init__(self, logger: logging.Logger, errors: list[dict]):
        delimiter = "\n\t- "
        self.message = (f"Structured data submission failed due to the following error(s):"
                        f"{delimiter}{delimiter.join(parse_pydantic_errors(errors))}\n Please see "
                        f"https://www.ebi.ac.uk/biosamples/docs/references/api/submit#_submit_structured_data for more "
                        f"information")
        logger.error(self.message)
        super().__init__(self.message)

class StructuredDataSubmissionError(Exception):
    def __init__(self, logger: logging.Logger, response: Response):
        self.message = f"Error submitting structured data: {response.text}"
        logger.error(self.message)
        super().__init__(self.message)

class EnaNoSubmissionProvidedError(Exception):
    def __init__(self, logger: logging.Logger):
        self.message = f"No EnaSubmission was provided in the list of entities; need to provide one."
        logger.error(self.message)
        super().__init__(self.message)

class EnaAccessionTypeNotFound(Exception):
    def __init__(self, logger: logging.Logger, accession: str):
        self.message = f"Accession {accession} type not found; please ensure there are no typos."
        logger.error(self.message)
        super().__init__(self.message)

class EnaInvalidEntityError(Exception):
    def __init__(self, logger: logging.Logger, entity_name: str):
        self.message = (f"Entity {entity_name} is not a valid entity for submission to ENA. If you think this is a bug, "
                        f"please report to https://github.com/ESapenaVentura/biobroker/issues.")
        logger.error(self.message)
        super().__init__(self.message)

class EnaInvalidEntityTypeError(Exception):
    def __init__(self, logger: logging.Logger, entity_name: str, found_entity_type_list: set, expected_entity_type: str):
        self.message = (f"For the list of entities of type {entity_name}, found the following entity types: "
                        f"{','.join(found_entity_type_list)}. Expected entity type: {expected_entity_type}.")
        logger.error(self.message)
        super().__init__(self.message)


class EnaSubmissionError(Exception):
    def __init__(self, logger: logging.Logger, error_list: list):
        formatted_error_list = {}
        for error in error_list:
            if error.startswith('File '):
                entity_type = 'Files'
                alias = error.split(' ')[1]
                error_message = " ".join(error.split(' ')[2:])
            elif error.startswith('Failed to'):
                entity_type = error.split(' ')[3]
                alias = error.split('"')[1]
                error_message = error.split(', ')[1]
            else:
                entity_type = error.split(',')[0].replace('In ', '')
                alias = error.split('"')[1]
                error_message = error.split('. ')[1]
            if entity_type not in formatted_error_list:
                formatted_error_list[entity_type] = []
            formatted_error_list[entity_type].append(f"Alias '{alias}': {error_message}")
        message_delimiter = "\n\t- "
        error_messages = "\n".join([f"{entity_type}:\n\t- {message_delimiter.join(formatted_error_list[entity_type])}"
                                    for entity_type in formatted_error_list])
        self.message = (f"Errors found when applying operations to ENA:\n{error_messages}\nIf you think this is an error,"
                        "please report to ENA helpdesk (https://www.ebi.ac.uk/ena/browser/support) or open an issue"
                        "on https://github.com/ESapenaVentura/biobroker/issues")
        logger.error(self.message)
        super().__init__(self.message)