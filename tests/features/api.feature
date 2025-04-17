Feature: API unit tests

  Background: API instances are pre-loaded
    Given all the API classes and their corresponding authenticator

  Scenario Outline: Submit and retrieve functions
    Given <length> <metadata_entity> filled with content from <metadata_json_path>
    When an API instance named <api_instance_name> is used to submit it to the archive
    Then we get a list of entities with the expected length and the accession set up
    And retrieving those entities by accession should result in the exact same entities

    Examples: BsdApi
    | length | metadata_entity | metadata_json_path        | api_instance_name     |
    | 1 | Biosample | assets/biosamples_valid_minimal.json | BsdApi                |
    | 2 | Biosample | assets/biosamples_valid_minimal.json | BsdApi                |
    | 1 | WebinV2Api | assets/ena_valid_minimal.json       | WebinV2Api            |
    | 2 | WebinV2Api | assets/ena_valid_minimal.json       | WebinV2Api            |

  Scenario Outline: Update function
    Given <length> <metadata_entity> filled with content from <metadata_json_path>
    When an API instance named <api_instance_name> is used to update the entity
    Then we get a list of entities with the expected length and the updated metadata

    Examples: BsdApi
    | length | metadata_entity | metadata_json_path               | api_instance_name     |
    | 1 | Biosample | assets/accessioned_BsdApi_entity.json       | BsdApi                |
    | 2 | Biosample | assets/accessioned_BsdApi_entity.json       | BsdApi                |
    | 1 | EnaStudy  | assets/accessioned_WebinV2Api_entity.json  | WebinV2Api            |
    | 2 | EnaStudy  | assets/accessioned_WebinV2Api_entity.json  | WebinV2Api            |

  Scenario Outline: Delete function
    Given <length> <metadata_entity> filled with content from <metadata_json_path>
    When an API instance named <api_instance_name> is used to delete the entity
    Then the entity should be deleted

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

  Scenario: File upload, retrieval and deletion - Valid file (WebinV2Api)
    Given a valid file object
    When the file is uploaded to WebinV2Api
    Then it should return a success message with the file ID
    And the file should be retrievable by its ID

  Scenario: File upload, retrieval and deletion - Invalid file (WebinV2Api)
    Given a valid file object
    When the file is uploaded to WebinV2Api but it fails to upload
    Then it should raise an error with the expected error messages
    And the file should not be retrievable by its ID