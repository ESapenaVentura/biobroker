## User notes
- If you're unsure as to what to fill out for each entity, please refer to the class staticmethod `guidelines()`. This
should provide you with enough information to fill out a basic Metadata entity
  - For BioSamples, please note: if you're validating against a checklist, the guidelines don't include the mandatory
  properties for the checklist. For that, refer to the checklist you're using.
- Please, PLEASE, unless the archive allows it, don't put units in the field's name. This is not very demure; not very
classy. Instead, create another field to indicate the units or use archive functionality for it. For example, in
BioSamples, a field is allowed to have a `unit` tag, and you can specify the units there alongside the value. THAT is
demure. That is mindful. You're not like the other users.

## Developer notes
- Please provide users with a `guidelines()` method in any subclass that you create. I get it; it's cumbersome, you're 
and expert of that archive and for you all this information is very basic. But I am sure you've input your pin wrongly
before because the numpad had the inverse notation (Fun fact: [There's a reason for that](https://ux.stackexchange.com/questions/16666/why-do-numpads-on-keyboards-and-phones-have-reversed-layouts)),
so just **WRITE IT**. It takes 5 seconds.

## TO-DO

BsdApi:
- When submitting multiple entities, it iterates in chunks of x size - If a chunk fails, the previous would have been
  already submitted, but that batch and the batches onwards will fail - Thinking about validating samples before doing
  a batch submission, but that may make the process way slower. Need to test speed for that.
- Add the missing relationship types, don't be lazy
- Add a way to delete the samples (empty put, basically)
- **KNOWN BUG**: Multiple relationships may not be added correctly with '__setitem__'
- **KNOWN BUG**: The order of the factors does alter the product. Accession needs to be set-up first in order for some of the '__setitem__' checks to go through correctly. Whoopsie.
- Add support to flatten organisations