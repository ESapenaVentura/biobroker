Feature: Input processor unit tests

  Scenario Outline: Load metadata from source
    Given an instance of <input_processor> loaded with an <input_file>
    When I have a JSON file with the same content
    Then the input_data must be the same as the JSON file

    Examples: TSV
      | input_processor   | input_file              |
      | TsvInputProcessor | assets/valid_minimal.tsv|

    Examples: XLSX
      | input_processor   | input_file                |
      | XlsxInputProcessor | assets/valid_minimal.xlsx |

  Scenario Outline: Transform method
    Given an instance of <input_processor> loaded with an <input_file>
    When I call the transform function on the data with a map
    Then the input_data key 'other_field' must be named 'new_field'

    Examples: TSV
      | input_processor   | input_file              |
      | TsvInputProcessor | assets/valid_minimal.tsv|

    Examples: XLSX
      | input_processor   | input_file                  |
      | XlsxInputProcessor | assets/valid_minimal.xlsx  |

  Scenario Outline: Integration with Metadata Entities
    Given an instance of <input_processor> loaded with an <input_file>
    When I call the process method providing with a <metadata_entity_class> class
    Then it should result in a valid Metadata Entity

    Examples: BioSamples
      | input_processor   | input_file                | metadata_entity_class |
      | TsvInputProcessor | assets/valid_minimal.tsv  | Biosample             |
      | XlsxInputProcessor| assets/valid_minimal.xlsx | Biosample             |