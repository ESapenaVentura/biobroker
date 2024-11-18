Feature: Metadata entity unit tests

  Background: Metadata entity instances are pre-loaded
    Given all the metadata entity classes


  Scenario Outline: Flatten method
    Given a <metadata_entity>
    When the flatten method is called
    Then it should result in a non-nested dictionary

    Examples: Biosample
    | metadata_entity |
    | Biosample       |

  Scenario Outline: Adding values as a dictionary
    Given a <metadata_entity>
    When I add a set of key:value pairs
    Then they should be loaded in the entity in the proper place

    Examples: Biosample
    | metadata_entity |
    | Biosample       |

  Scenario Outline: Deleting values as a dictionary
    Given a <metadata_entity>
    When I delete a value
    Then it should be deleted from the entity

    Examples: Biosample
    | metadata_entity |
    | Biosample       |

  Scenario: Biosample - Add relationship
    Given a Biosample
    When I add a valid relationship
    Then it should be loaded at the root, under 'relationships'

  Scenario: Biosample - Add external reference
    Given a Biosample
    When I add a valid external reference
    Then it should be loaded at the root, under 'external_references'
