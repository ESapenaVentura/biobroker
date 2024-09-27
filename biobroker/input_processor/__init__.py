"""
Input metadata processor. The goal of this module is to take an input file, read it and transform it into a list of
dictionaries containing the metadata for the different entities. Once in a flattened JSON state, they can be processed
into all the different entities.

**Mandatory arguments**:

- input_data: Path to the input file or loaded content. To be decided by subclass processor.

**Optional arguments**:

- verbose: set to `True` if you want `INFO` and above-level logging events. If not set or set to False, only `WARNING`
  and above will be displayed

**Subclasses of GenericInputProcessor must define the following methods/properties**:

- @input_data.setter

**Aspects to improve**:

- Currently, the :func:`~biobroker.input_processor.GenericInputProcessor.process`
  function can fail at any point if any entity fails to validate. This could be handled in 2 ways:

    - Catch all exceptions (meh) log them, and create the rest of the entities.
    - `Current behaviour`: fail miserably and not return anything. I really like this option as, for me, an input
      (spreadsheet, tsv file, etc) probably has meaning together and should remain this way. It could
      be improved by logging all errors, then failing.
"""

from .input_processor import GenericInputProcessor, TsvInputProcessor, XlsxInputProcessor
__all__ = ['GenericInputProcessor', 'TsvInputProcessor', 'XlsxInputProcessor']
