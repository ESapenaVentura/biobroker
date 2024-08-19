import logging
import json

from json.decoder import JSONDecodeError


def parse_checklist_validation_errors(response_text: str):
    """
    Parse a checklist validation error and return it in a printable state.

    :param response_text: Response text from the validation/submission request that failed checklist validation.
    :return: printable string.
    """
    validation_errors = json.loads(response_text.split('failed: ')[2])
    validation_errors_str = "\n\t- ".join([f"{validation_errors[i]['dataPath']}: "
                                           f"{','.join(validation_errors[i]['errors'])}"
                                           for i in range(len(validation_errors))])
    return validation_errors_str


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
    def __init__(self, sample_id, response, logger: logging.Logger):
        """
        Raise when an error comes from an API update request.

        :param sample_id: Id of the sample that raised the error
        :param response: errored response (r.status_code >= 300)
        :param logger: subclasss logger to log the error message to.
        """
        try:
            message = f"Sample with ID {sample_id} can't be updated - Error: {response.json()['error']}"
        except JSONDecodeError:
            # Validation against checklist failed, returns a non-jsonable message
            validation_errors_str = parse_checklist_validation_errors(response.text)
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
        message = f"Sample with ID {sample_id} can't be updated - Error(s): \n\t- {reasons_str}"
        logger.error(message)
        super().__init__(message)


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
        validation_errors_str = parse_checklist_validation_errors(response_text)
        message = f"Samples failed checklist validation with the following errors: \n\t- {validation_errors_str}"
        logger.error(message)
        super().__init__(message)
