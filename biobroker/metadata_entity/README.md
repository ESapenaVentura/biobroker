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

## Extra functionality (Defined only in specific entities)

### BioSample - Unit curation

A good practice is to parse the strings being assigned to the metadata entity, and try to identify if they are units.

However, that doesn't mean that it will be overwritten. We have warnings for that. Trying to identify automatically will
result in excel-level gene symbol horror (remember that?), so the Biosample entity does warn you and provide you with
the tools to correct it yourself.

**Modify your data to include the units!!!!**