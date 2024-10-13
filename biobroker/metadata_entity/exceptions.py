import logging
from biobroker.generic.utilities import parse_pydantic_errors

class EntityValidationError(Exception):
    def __init__(self, logger: logging.Logger, entity_id: str, errors: list[dict]):
        delimiter = "\n\t- "
        self.message = (f"Metadata content has failed validation for '{entity_id}':"
                        f"{delimiter}{delimiter.join(parse_pydantic_errors(errors))}")
        logger.error(self.message)
        super().__init__(self.message)

class NoNameSetError(Exception):
    """Name has not been set in the sample"""
    def __init__(self, logger: logging.Logger, sample_id: str):
        self.message = f"Property 'name' needs to be set-up for the sample '{sample_id}'"
        logger.error(self.message)
        super().__init__(self.message)


class NameShouldBeStringError(Exception):
    """Name should be a string, no other types allowed"""
    def __init__(self, logger: logging.Logger, name):
        self.message = f"Property 'name' should be a string. Current value: {name}"
        logger.error(self.message)
        super().__init__(self.message)


class RelationshipInvalidSourceError(Exception):
    """Invalid source for relationship"""
    def __init__(self, logger: logging.Logger, sample_id: str, source: str):
        self.message = (f"Sample {sample_id}: invalid relationship source '{source}'. Only Biosample accessions can be "
                        "used")
        logger.error(self.message)
        super().__init__(self.message)


class RelationshipInvalidTargetError(Exception):
    """Invalid target for relationship"""
    def __init__(self, logger: logging.Logger, sample_id: str, target: str):
        self.message = (f"Sample {sample_id}: invalid relationship target '{target}'. Only Biosample accessions can be "
                        "used")
        logger.error(self.message)
        super().__init__(self.message)

class NoOrganismSetError(Exception):
    def __init__(self, logger: logging.Logger, sample_id: str):
        self.message = f"Property 'organism' (Or any variant) needs to be set-up for the sample '{sample_id}'"
        logger.error(self.message)
        super().__init__(self.message)
