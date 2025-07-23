# Local Runtime

## Pregal Loop

## Pregal Loop


1. **Enqueue external events**: check `_externalMessages` and add them to current execution `messageChannel` queue.
2. **Enqueue Step Messages**: using `step.GetAllEvents()` get all events emitted by all steps in previous iteration and add them to current execution `messageChannel` queue.
3. **Exit check**:
    - No more messages in `messageChannel` queue.
    - No more external messages getting added to `_externalMessages`.
    - `!keepAlive`?

4. **Process messages**: process messages added to `messageChannel` queue and inject them to matching step event/edges with `step.HandleMessageAsync()`.

5. **Wait all step with new messages**: wait all steps with new messages to finish processing new messages. `Task.WhenAll(messageTasks)`.

## Requirements

- Should only save to storage at the end of pregal superstep iteration.
- Should allow saving intermediate state locally while superstep steps finish running.
- Should allow reading from storage only at process initialization.
- In other instances reading happens from local storage manager.
- For steps:
    - save/read step info (name, runningId, parentId, status[does not exist now])
    - save/read step events (edgeGroups messages)
    - save/read step state (if any)
- For process:
    - save/read process info (name, runningId, children name:running id mapping)
    - save/read process events (pending external messages)
    - save/read process state (does not exist now)


## Checkpointing

```mermaid
sequenceDiagram  
    participant External as External System  
    participant Process as Parent Process  
    participant Step as Step  
    participant PSM as ProcessStorageManager  
    participant IPSC as IProcessStorageConnector  
  
    External->>+Process: Start Process
    Process-->>+PSM: Initialize Process Storage Manager
    Process-->>PSM: Fetch Process Data From Storage
    PSM-->>+IPSC: ReadEntryFromStorage - Process Data
    IPSC-->>-PSM: Process Data Retrieved
    PSM->>+PSM: Save Process Data locally

    Process-->>+PSM: Get Process Data
    PSM-->>-Process: Process Data Retrieved

    loop over Steps
        Process->>Process: Create Local Steps with existing runningIds
    end
    loop over Steps
        Process-->>+PSM: Fetch Step Data from Storage
        PSM-->>+IPSC: ReadEntryFromStorage - Step Data
        activate IPSC
        IPSC-->>-PSM: Step Data Retrieved
        PSM->>+PSM: Save Step Data locally
    end
    loop over superSteps
        Process->>Process: Enqueue External Messages
        Process->>Process: Enqueue Step Messages

        Process->>+Step: Get Step Events
        Step-->>-Process: Step Events Retrieved (if any)

        Process->>Process: Exit Check (any messages to be processed)
        alt no messages to be processed
            Process->>External: Exit Process
        end


        Process->>Process: Process Messages
        loop over messages to be distributed
            Process->>Process: Find matching Step for message
            Process-->>+Step: step.HandleMessageAsync
            alt step is not initialized
                Step-->>Step: Start Step Initialization
                Step-->>+PSM: Get Step State
                PSM-->>-Step: Step State Retrieved
                Step-->>-Step: Apply saved state to step
                Step-->>+PSM: Get Step Events
                PSM-->>-Step: Step Events Retrieved
                Step-->>Step: Apply pending events if any to edgeGroups
            end

            alt edgeGroup has all required messages
                Step-->>PSM: Save EdgeGroup Messages
                Step-->>+Step: Execute Step
                Step-->>PSM: Save Step State
                Step-->>PSM: Save Reset EdgeGroup Messages
                Step-->>-Process: Step Execution Completed
            else
                Step-->>PSM: Save EdgeGroup Messages
                Step-->>Process: Skipping Step Execution
            end
        end

        Process-->>Process: Wait for all steps to finish processing messages

        Process-->>+PSM: Save Process Data (State, External Messages)
        Process-->>PSM: Save Process Data to Storage
        PSM-->>IPSC: WriteEntryToStorage - Process Data
        Process-->>PSM: Save children Steps Data to Storage
        PSM-->>IPSC: WriteEntryToStorage - Step Data

    end


   
```