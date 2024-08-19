import logging


class UsernameNotValid(Exception):
    """Username is not deemed valid for the authenticator"""
    def __init__(self, username: str, logger: logging.Logger):
        message = f"Bad username provided: '{username}'. Maybe you meant to use another authenticator?"
        logger.error(message)
        super().__init__(message)


class WrongUserOrPassword(Exception):
    """Wrong username or password provided to authenticator"""
    def __init__(self, username: str, password: str, logger: logging.Logger):
        message = f"Bad user or password: username={username}, password={password}"
        logger.error(message)
        super().__init__(message)


class DomainAlreadyExists(Exception):
    """Domain already exists"""
    def __init__(self, domain: str, logger: logging.Logger):
        message = f"Domain '{domain}' already exists in AAP. Please try another name"
        logger.error(message)
        super().__init__(message)
