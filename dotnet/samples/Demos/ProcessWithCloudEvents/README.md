# Process With Cloud Events

The following demos describe how to use the SK Process Framework to emit and receive cloud events.

| Project | Description |
| --- | --- |
| ProcessWithCloudEvents.Processes | Project that contains Process Builders definitions, related steps, models and structures independent of runtime |
| ProcessWithCloudEvents.Grpc | Project that contains a gRPC server using DAPR, that interacts with processes defined in the Processes project using gRPC |
| ProcessWithCloudEvents.Client | Project that contains a ReactJS App to showcase sending and receiving cloud events to and from a running SK Process in a server |

## Processes

### Document Generation Process

This SK process emulates the interaction of a user requesting for some document generation for a specific product. This includes:

1. **Gather Product Info Step**: Product Information Fetching
2. **Generate Documentation Step - `GenerateDocs`**: Document Generation
3. **Proof Read Documentation Step**: Document Proof Reading to validate the generate document
4. **Proxy Step**: Request for user approval of the generated document
5. **Publish Documentation Step**: Publish the generated document once the user approves it
6. **Generate Documentation Step - `ApplySuggestions`**: Document suggestions addition if the user rejects the generated document
7. **Proxy Step**: Publish generated document externally

``` mermaid
graph LR
    StartDocumentGeneration([StartDocumentGeneration<br/>Event])
    UserRejectedDocument([UserRejectedDocument<br/>Event])
    UserApprovedDocument([UserApprovedDocument<br/>Event])

    GatherProductInfo["Gather Product Info <br/> Step"]
    GenerateDocs["Generate Documentation <br/> Step"]
    ProofReadDocs["Proof Read Documentation <br/> Step"]
    Proxy["Proxy <br/> Step"]
    PublishDocs["Publish Documentation <br/> Step"]
    
    GatherProductInfo --> GenerateDocs --> |DocumentGenerated| ProofReadDocs --> PublishDocs
    ProofReadDocs --> |DocumentApproved| Proxy
    ProofReadDocs -->|DocumentRejected| GenerateDocs

    PublishDocs --> Proxy

    StartDocumentGeneration --> GatherProductInfo
    UserRejectedDocument --> GenerateDocs
    UserApprovedDocument --> PublishDocs
```

- To emit events from the SK Process externally, SK events are sent to the Proxy Step.
- To receive external events and send them to the SK Process, SK Input Events are linked externally and sent to the process.

## Setup

1. A custom server is created that launches the creation of a SK Process with a specific process id and a specific input event.
2. A custom implementation of the `IExternalKernelProcessMessageChannel` is injected containing the custom implementation of the Cloud Event channel to be used. The custom implementation must include:
    - `Initialize`: Initial setup to start the connection with the server.
    - `Uninitialize`: Logic needed to close the connection with the server.
    - `EmitExternalEventAsync`: Logic to send an external event to the server. This may include internal mapping of SK topics to specific server exposed methods.
3. Use of the `ProxyStep` in the `ProcessBuilder` to emit external events on specific SK Events. <br/>Example:
   ``` csharp
   var proxyStep = processBuilder.AddProxyStep([DocGenerationTopics.RequestUserReview, DocGenerationTopics.PublishDocumentation]);
   ...
   docsPublishStep
      .OnFunctionResult()
      .EmitExternalEvent(proxyStep, DocGenerationTopics.PublishDocumentation);
   ```

## Usage

1. Run the server running the SK Process using a specific Cloud Event technology
2. Launch the Client App to interact with the SK Process from a UI