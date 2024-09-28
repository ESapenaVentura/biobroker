## Notes for developers

- The functions `retrieve`, `update` and `submit` **MUST NOT** be overwritten by subclasses at any point. This function is just a wrapper for
  their hidden counterparts. For the developers of new subclasses, please overwrite those 2. Any implementation that 
  uses these classes will be expected to be able to call those functions.


## TO-DO list
- BsdApi: Add support for structured data
  - Add method `add_structured_data`
  - Add method `remove_structured_data`
  - Add method `get_structured_data`
  - Add method `get_structured_data_by_type`
- Additional errors needed:
  - Requests that get a 400 (e.g. Trying to update samples not owned by the user)