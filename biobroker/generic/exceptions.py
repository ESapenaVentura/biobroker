import inspect
import logging


class MandatoryFunctionNotSet(Exception):
    """Mandatory function has not been overriden in subclass"""
    def __init__(self, logger: logging.Logger):
        previous_frame = inspect.currentframe().f_back
        caller_function = previous_frame.f_code.co_name
        caller_function_parameters = previous_frame.f_code.co_varnames[1:previous_frame.f_code.co_argcount]
        caller_class = previous_frame.f_locals['self'].__class__.__name__
        message = f"Mandatory function '{caller_function}' not set in '{caller_class}'. Need to set up the following " \
                  f"parameters for the function: {', '.join(caller_function_parameters)}"
        logger.error(message)
        super().__init__(message)