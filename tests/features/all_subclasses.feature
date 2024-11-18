Feature: initialize classes

  Scenario Outline: Loading a subclass and testing mandatory methods and properties are set
    Given I have a <subclass_object> and its init arguments: <arguments>
    When I load the instance with the arguments
    Then it should have all mandatory fields and methods from the parent class <parent_class>

      Examples: Input processors
          | subclass_object   | arguments                     | parent_class           |
          | TsvInputProcessor | ["assets/valid_minimal.tsv"]  | GenericInputProcessor  |
          | XlsxInputProcessor| ["assets/valid_minimal.xlsx"] | GenericInputProcessor  |

      Examples: Output Processors
          | subclass_object    | arguments                    | parent_class            |
          | TsvOutputProcessor | ["assets/valid_minimal.tsv"] | GenericOutputProcessor  |
          | XlsxOutputProcessor| ["assets/valid_minimal.xlsx"]| GenericOutputProcessor  |


      Examples: Authenticator
          | subclass_object   | arguments                       | parent_class        |
          | WebinAuthenticator| ["function", "load_credentials_webin"]| GenericAuthenticator|

      Examples: API
          | subclass_object   | arguments                       | parent_class        |
          | BsdApi            | ["function", "load_webin_authenticator"]  | GenericApi|

      Examples: Metadata Entities
          | subclass_object   | arguments                                 | parent_class  |
          | Biosample         | ["function", "load_biosample_valid_json"] | GenericEntity |