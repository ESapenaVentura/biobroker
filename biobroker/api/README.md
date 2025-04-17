## Notes for developers

- The functions `retrieve`, `update` and `submit` **MUST NOT** be overwritten by subclasses at any point. This function is just a wrapper for
  their hidden counterparts. For the developers of new subclasses, please overwrite those 2. Any implementation that 
  uses these classes will be expected to be able to call those functions.


## TO-DO list

- Additional errors needed:
  - Requests that get a 400 (e.g. Trying to update samples not owned by the user)

Webinv2Api:
- Catching errors in self.upload_file ; currently assumes file upload always fails during upload, and not on e.g. authentication
- **improvement**: Check if file size in local vs remote is the same when uploading - if not, assume remote is corrupted and overwrite.