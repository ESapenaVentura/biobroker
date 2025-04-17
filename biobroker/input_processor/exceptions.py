"""
Placeholder submodule for input processor-related exceptions.
"""

import logging


class CantProcessBothEntityTypes(Exception):
    """Only entity or entities, not both, must be set up"""
    def __init__(self, logger: logging.Logger):
        self.message = f"Can't process; both entity and entities_map has been specified. Please choose one."
        logger.error(self.message)
        super().__init__(self.message)

class CantProcessNoEntityTypes(Exception):
    """At least one of entity or entities must be specified"""
    def __init__(self, logger: logging.Logger):
        self.message = f"Can't process; no entity or entities_map has been specified. Please specify one."
        logger.error(self.message)
        super().__init__(self.message)

class InputDataIsComplexError(Exception):
    """Input data can't be complex if entity is specified"""
    def __init__(self, logger: logging.Logger, keys: list[str]):
        self.message = (f"Can't process; input data is complex, but entity has been specified. Keys found: {keys}. "
                        f"Please pass 'entities_map' to the 'process' method instead.")
        logger.error(self.message)
        super().__init__(self.message)

class TooManyEntitiesSpecifiedError(Exception):
    """More entities specified than there are to process"""
    def __init__(self, logger: logging.Logger, entities: list[str]):
        self.message = (f"Can't process; there are more entities specified in the entities_map than there are in the input data. "
                        f"Entities specified: {entities}")
        logger.error(self.message)
        super().__init__(self.message)
