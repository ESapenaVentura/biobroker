"""
Metadata entities. The goal of this module is to define the metadata entities that each archive uses. All the metadata
is saved under the self.entity property, but the whole class can be accessed as a dictionary.

To make it easier for the users, it is expected that all properties can be accessed as a root property.
The subclasses then must define how properties are accessed by defining "__setitem__", "__getitem__" and "__contains__".
If unsure, look at the "Biosample" subclass to understand how this is implemented.

The base generic entity also defines a custom JSON encoder, to avoid JSON.dumps issues. Any class not serializable will
be turned to string.

**Mandatory arguments**:

    - metadata_content: Metadata content for the entity, in JSON format.
    - field_mapping: Map <archive_key_name>:<metadata_content_key_name> in JSON format
    - keep_non_mapped_fields: Boolean, wether to keep the non-mapped fields.

**Optional arguments**:

- verbose: set to `True` if you want `INFO` and above-level logging events. If not set or set to False, only `WARNING`
  and above will be displayed

**Subclasses of GenericEntity must define the following methods/properties**:

- @GenericEntity.setter
- id property
- accession property
- validate
- flatten
- dictionary special methods ('__setitem__', '__delitem__', '__getitem__', '__contains__')

**Subclasses of GenericEntity SHOULD define the following methods/properties**:

- guidelines

**Aspects to improve**:

- Biosamples entity: taxonId or organism must be set up. Currently allows entities to be created without those fields.
- Biosamples entity: Currently the root keys are hardcoded in the submodule. I wonder what would be the best way to
  indicate them without complicating the code and depending too much on external files. These are not bound to change
  much - but still, not good practice to have them in the code.
"""

from .metadata_entity import GenericEntity, Biosample

__all__ = ['GenericEntity', 'Biosample']
