import os
import sys

from openpyxl.styles.builtins import output

from biobroker.authenticator import WebinAuthenticator # Biosamples uses the WebinAuthenticator
from biobroker.api import BsdApi # BioSamples Database (BSD) API
from biobroker.metadata_entity import Biosample # The metadata entity
from biobroker.input_processor import TsvInputProcessor # An input processor
from biobroker.output_processor import XlsxOutputProcessor # An output processor

def create_sample_tsv():
    sample_tsv = [
        ["sample_id", "collected_at", "organism"],
        ["sumple", "noon", "Homo sapiens"]
    ]
    writable_sample = "\n".join(["\t".join(row) for row in sample_tsv])
    with open("simple_sample_sumple.tsv", "w") as f:
        f.write(writable_sample)

def load_samples_tsv():
    input_processor = TsvInputProcessor("simple_sample_sumple.tsv")
    return input_processor

def update_samples(submitted_samples: list[Biosample], api: BsdApi):
    for sample in submitted_samples:
        sample['newField'] = "newValue"
    return api.update(submitted_samples)

def main(webin_username, webin_password):
    create_sample_tsv()
    # Step 1: load your samples
    input_processor =  load_samples_tsv()
    ## 1.1: transform your metadata
    my_field_map = {"sample_id": "name"}
    input_processor.transform(field_mapping=my_field_map)
    ## 1.2: Process them into Biosample objects
    my_samples = input_processor.process(Biosample)

    # Step 2: Set-up authenticator + webin
    os.environ['API_ENVIRONMENT'] = "dev"  # Dev
    authenticator = WebinAuthenticator(username=webin_username, password=webin_password)
    api = BsdApi(authenticator=authenticator)

    # Step 3: Submit
    my_submitted_samples = api.submit(my_samples)

    # Step 4: Retrieve (I know, they're just up there - just showcasing)
    my_submitted_samples = api.retrieve([sample.accession for sample in my_submitted_samples])

    # Step 5: Update
    my_updated_samples = update_samples(submitted_samples=my_submitted_samples, api=api)

    # Step 6: profit (Aka, just get your spreadsheet and get outta here)
    output_processor = XlsxOutputProcessor('my_updated_samples.xlsx')
    output_processor.save(my_updated_samples)



if __name__ == '__main__':
    webin_username = sys.argv[1]
    webin_password = sys.argv[2]
    main(webin_username, webin_password)