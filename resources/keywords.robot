*** Settings ***
Documentation    Shareable resource within the robot containing commonly available
...    keywords.

Variables    variables.py


*** Keywords ***
Log Today In RF
    [Documentation]    Displays today's date in Robot Framework.

    Log    Today is ${TODAY}. (from RF)

My Resource Keyword
    [Documentation]    Describe what this pure RF keyword does.
    [Arguments]    ${var}=test

    Log    RF keyword executed with value: ${var}

    RETURN    ${var}
