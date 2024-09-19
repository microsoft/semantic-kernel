*** Settings ***
Documentation    Robot Framework template implementing a Producer-Consumer model using
...    custom libraries and resources. (Reporter robot which reports Consumer's results)

Library    RPA.Robocorp.WorkItems

Variables    variables.py


*** Keywords ***
Count Input
    [Documentation]    Retrieve and print post-process item details.

    ${processed_data} =    Get Work Item Variable    processed_data
    ${message} =    Get Work Item Variable    message
    Log    Item processed data: ${processed_data}
    Log    Item observation: ${message}

    RETURN    ${1}  # the item was fully successfully processed


*** Tasks ***
Report Result
    [Documentation]    Generate a report comprising all the details of the previously
    ...    processed items.

    IF    not "%{CREATE_REPORT=}"
        Fail    Reporting is disabled!
    END

    # NOTE: The reporter might work best when it waits for all the Work Items in the
    #  previous Step to be finished, so it can collect all the inputs in a single run.
    #  This "Step Sync" feature is currently on the TODO list in Control Room.
    @{results} =    For Each Input Work Item    Count Input
    ${total} =    Evaluate    sum(${results})
    Log    Successfully processed items: ${total}

    Log To Console    Done with processing all the input Work Items (Consumer outputs).
