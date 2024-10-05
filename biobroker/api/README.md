## Notes for developers

- The functions `retrieve`, `update` and `submit` **MUST NOT** be overwritten by subclasses at any point. This function is just a wrapper for
  their hidden counterparts. For the developers of new subclasses, please overwrite those 2. Any implementation that 
  uses these classes will be expected to be able to call those functions.


## TO-DO list

- Additional errors needed:
  - Requests that get a 400 (e.g. Trying to update samples not owned by the user)