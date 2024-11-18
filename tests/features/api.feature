Feature: API unit tests

  Background: API instances are pre-loaded
    Given all the API classes and their corresponding authenticator

  Scenario Outline: Submit and retrieve functions
    Given <length> <metadata_entity> filled with content from <metadata_json_path>
    When an API instance named <api_instance_name> is used to submit it to the archive
    Then we get a list of entities with the expected length and the accession set up
    And retrieving those entities by accession should result in the exact same entities

    Examples: BsdApi
    | length | metadata_entity | metadata_json_path | api_instance_name |
    | 1 | Biosample | assets/valid_minimal.json | BsdApi                |
    | 2 | Biosample | assets/valid_minimal.json | BsdApi                |

  Scenario Outline: Update function
    Given <length> <metadata_entity> filled with content from <metadata_json_path>
    When an API instance named <api_instance_name> is used to update the entity
    Then we get a list of entities with the expected length and the updated metadata

    Examples: BsdApi
    | length | metadata_entity | metadata_json_path | api_instance_name |
    | 1 | Biosample | assets/accessioned_BsdApi_entity.json | BsdApi                |
    | 2 | Biosample | assets/accessioned_BsdApi_entity.json | BsdApi                |

  Scenario: Structured data - Invalid data (Biosamples)
    Given an invalid structured data object
    When the structured data is submitted to Biosamples
    Then it should raise an error with the expected error messages


  Scenario: Structured data - Invalid accession (Biosamples)
    Given a valid structured data object with an invalid accession
    When the structured data is submitted to Biosamples
    Then it should raise an error regarding the accession