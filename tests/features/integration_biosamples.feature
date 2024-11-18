Feature: Submission to Biosamples - Integration

  Background: Set up entities
    Given an input excel file and all the biobroker entities set up

  Scenario: Submit a valid sample from an excel file
    When I submit using the BsdApi
    Then the samples should be correctly submitted
    And I can save it again as an excel file

  Scenario: Submit a sample validating against checklist ERC000022 - Fail
    When I add checklist ERC000017 to the sample and submit
    Then the sample should raise errors related to the checklist

  Scenario: Submit a sample validating against checklist ERC000022 - Success
    When I add checklist ERC000017 to the sample and submit
    And I modify the metadata to contain the mandatory fields for the checklist
    And I submit using the BsdApi
    Then the samples should be correctly submitted
    And I can save it again as an excel file