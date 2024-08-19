from __future__ import annotations

from typing import TYPE_CHECKING

import os
import logging
import progressbar

# Need this to not hit a circular import issue with type hints
if TYPE_CHECKING:
    from broker.api import GenericApi
    from broker.authenticator import GenericAuthenticator
    from broker.input_processor import GenericInputProcessor
    from broker.output_processor.generic_output_processor import GenericOutputProcessor
    from broker.metadata_entity.generic_entity import GenericEntity
    from broker.wrangler.wrangler import Wrangler


progressbar.streams.wrap_stderr()  # This is needed for progressbar to work around loggers.


def set_up_logger(instance_object: GenericApi | GenericAuthenticator | GenericEntity | GenericInputProcessor |
                  GenericOutputProcessor | Wrangler, verbose: bool = False) -> logging.Logger:
    """
    Set up logger for any instance of a class.

    :param instance_object: Instance of the object being initialised.
    :param verbose: If true, set StreamHandler to INFO. If False, set to WARNING.
    :return: logging.Logger instance initialised to the class.
    """
    level = logging.INFO if verbose else logging.WARNING
    logger = logging.getLogger(instance_object.__class__.__name__)
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(os.environ.get('BROKER_LOG', default='broker_log.txt'))
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)  # File always set to level DEBUG
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(level)
    logger.addHandler(stream_handler)
    return logger
