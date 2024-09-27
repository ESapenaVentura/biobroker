"""
Output metadata processor. The goal of this module is to take an input list of GenericEntity's, transform it into a
dataframe and save it with pandas functionality into different formats. Pretty simple!

**Mandatory arguments**:

- output_path: Path to the file to save the metadata.

**Optional arguments**:

- verbose: set to `True` if you want `INFO` and above-level logging events. If not set or set to False, only `WARNING`
           and above will be displayed

**Subclasses of GenericOutputProcessor must define the following methods/properties**:

- _save
"""

from .output_processor import GenericOutputProcessor, TsvOutputProcessor, XlsxOutputProcessor

__all__ = ['GenericOutputProcessor', 'TsvOutputProcessor', 'XlsxOutputProcessor']
