Feature: Input processor unit tests

  Scenario Outline: Save metadata to source
    Given an instance of <output_processor> and a <metadata_entity> subclass loaded with the content in <valid_minimal_json>
    When I save the entity as <output_file_path>
    Then the output should be equal to <test_file_path>

    Examples: TSV
      | output_processor  | metadata_entity         | valid_minimal_json | output_file_path | test_file_path |
      | TsvOutputProcessor | Biosample  | assets/valid_minimal.json      | output.tsv       | assets/valid_minimal_test.tsv |

    Examples: XLSX
      | output_processor  | metadata_entity         | valid_minimal_json | output_file_path | test_file_path |
      | XlsxOutputProcessor | Biosample  | assets/valid_minimal.json      | output.xlsx       | assets/valid_minimal_test.xlsx |