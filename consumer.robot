*** Settings ***
Documentation    Robot Framework template implementing a Producer-Consumer model using
...    custom libraries and resources. (Consumer robot which consumes input work)

Library    DummyLibrary
Library    RPA.Robocorp.WorkItems

Resource    keywords.robot

Variables    variables.py


*** Keywords ***
Validate Input
    [Documentation]    Checks input data against a pattern and returns the status.
    [Arguments]    ${data}

    ${pattern} =    Set Variable    ^\\d+\\..*\\(${TODAY}\\)$
    ${match_ok} =    Run Keyword And Return Status    Should Match Regexp
    ...    ${data}    ${pattern}
    IF    ${match_ok}
        RETURN    ${True}    Item content is valid.
    END

    RETURN    ${False}    Data "${data}" doesn't match with "<number>.*(${TODAY})"!

Process Input
    [Documentation]    Processes input data and releases a BUSINESS failure for any
    ...    invalid item. If reporting is enabled, a new output Work Item is created
    ...    with its post-process info. (items failed to be processed due to APPLICATION
    ...    errors can be retried in Control Room)

    # Retrieve and validate the input data given the current item in the queue.
    ${data} =    Get Work Item Variable    data
    ${status}    ${message} =    Validate Input    ${data}

    # Release the item containing invalid data without retrying.
    IF    not ${status}
        Log    Invalid data due to: ${message}    level=WARN
        Release Input Work Item    FAILED    exception_type=BUSINESS
        ...    code=INVALID_DATA    message=${message}
        RETURN
    END

    # Try processing the validated input data and release the item for a later retry on
    #  failure.
    Log    Processing item data: ${data}...
    TRY
        ${processed_data} =    My Resource Keyword    ${data}
        ${processed_data} =    My Library Keyword    ${processed_data}
    EXCEPT    AS    ${error}
        Log    Bad data processing due to: ${error}    level=ERROR
        ${message} =    Set Variable    ${error}
        ${processed_data} =    Set Variable    ${None}
    END

    # Optionally create additional outputs for the report computed at Step 3.
    IF    "%{CREATE_REPORT=}"
        &{variables} =    Create Dictionary
        ...    processed_data    ${processed_data}
        ...    message    ${message}
        Create Output Work Item    variables=${variables}    save=${True}
    END

    # Release the app failures at the end so the optional output creation above can
    #  take place.
    IF    "${processed_data}" == "${None}"
        Release Input Work Item    FAILED    exception_type=APPLICATION
        ...    code=BAD_PROCESSING    message=${message}
    END


*** Tasks ***
Consume Input
    [Documentation]    Read and process the output Work Items from the 1st Step and
    ...    optionally create output ones (the result) as inputs for the 3rd Step.

    For Each Input Work Item    Process Input    return_results=${False}
    Log To Console    Done with processing all the input Work Items (Producer outputs).
