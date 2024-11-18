Feature: Authenticator unit tests

  Scenario Outline: Authenticator points to development and returns token
    Given a <auth> and a set of credentials loaded from '.env' with prefix <prefix>
    When I load the instance
    Then the auth endpoint should point to development
    And the token should conform to pattern <pattern>

    Examples: Webin
    | auth | prefix | pattern |
    | WebinAuthenticator | WEBIN | ^Bearer [\w-]+\.[\w-]+\.[\w-]+$ |