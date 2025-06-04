# Process With Cloud Events - using gRPC

For using gRPC, this demo follows the guidelines suggested for any [gRPC ASP.NET Core App](https://learn.microsoft.com/en-us/aspnet/core/grpc/test-tools?view=aspnetcore-9.0).

Which for this demo means:

- Making use of `builder.Services.AddGrpcReflection()` and `app.MapGrpcReflectionService()`
- Making use of [`gRPCui`](https://github.com/fullstorydev/grpcui) for testing

## Explanation

This demo showcases how SK Process Framework could interact with a gRPC Server and clients.

The main difference of this demo is the custom implementation of the gRPC Server and client used internally by the SK Process in the SK Proxy Step.

Main gRPC components:

- `documentationGenerator.proto`: `<root>\dotnet\samples\Demos\ProcessWithCloudEvents\ProcessWithCloudEvents.Grpc\Protos\documentationGenerator.proto`
- gRPC Server: `<root>\dotnet\samples\Demos\ProcessWithCloudEvents\ProcessWithCloudEvents.Grpc\Services\DocumentGenerationService.cs`
- gRPC Client/IExternalKernelProcessMessageChannel implementation: `<root>\dotnet\samples\Demos\ProcessWithCloudEvents\ProcessWithCloudEvents.Grpc\Clients\DocumentGenerationGrpcClient.cs`

### SK Process and gRPC Events

``` mermaid

sequenceDiagram
    participant grpcClient as gRPC Client
    box Server
        participant grpcServer as gRPC Server
        participant SKP as SK Process
    end

    grpcClient->>grpcServer: UserRequestFeatureDocumentation <br/>gRPC
    grpcServer->>SKP: StartDocumentGeneration <br/>SK event
    SKP->>grpcServer: RequestUserReview (SK Topic)/<br/>RequestUserReviewDocumentationFromProcess (gRPC)
    grpcServer->>grpcClient: RequestUserReviewDocumentation <br/>gRPC
    grpcClient->>grpcServer: UserReviewedDocumentation <br/>gRPC
    grpcServer->>SKP: UserApprovedDocument/UserRejectedDocument <br/>SK event
    SKP->>grpcServer: PublishDocumentation (SK Topic)/<br/>PublishDocumentation (gRPC)
    grpcServer->>grpcClient: ReceivePublishedDocumentation <br/>gRPC
```
1. When the `UserRequestFeatureDocumentation` gRPC request is received from the gRPC client, the server initiates an SK Process and emits the `StartDocumentGeneration` SK event.
2. The `RequestUserReview` topic is emitted when the `DocumentationApproved` event is triggered during the `ProofReadDocumentationStep`. This event invokes the `RequestUserReviewDocumentationFromProcess` gRPC method to communicate with the server.
3. The `RequestUserReviewDocumentationFromProcess` method updates the shared stream, which is used to communicate with the subscribers of `RequestUserReviewDocumentation`. The gRPC client then receives the document for review and approval.
4. The gRPC client can approve or reject the document using the `UserReviewedDocumentation` method to communicate with the server. The server then sends the `UserApprovedDocument` or `UserRejectedDocument` SK event to the SK Process.
5. The SK Process resumes, and the `PublishDocumentationStep` now has all the necessary parameters to execute. Upon execution, the `PublishDocumentation` topic is triggered, invoking the `PublishDocumentation` method on the gRPC server.
6. The PublishDocumentation method updates the shared stream used by `ReceivePublishedDocumentation`, ensuring that all subscribers receive the update of the latest published document
## Demo
### Requirements

- Have Dapr setup ready
- Build and Run the app
- Interact with the server by:
    - Install and run `gRPCui` listening to the address `localhost:58641`:
        ```
        ./grpcui.exe -plaintext localhost:58641
        ```

        or

    - Use the `ProcessWithCloudEvents.Client` App and use it to interact with the server. This app uses gRPC Web, which interacts with the server through `localhost:58640`.

### Usage without UI

For interacting with the gRPC server, the

1. Build and run the app
2. Open 2 windows of `gRPCui` with the following methods:
    - Window 1: 
        - Method name: `UserRequestFeatureDocumentation` and `UserReviewedDocumentation`
    - Window 2:
        - Method name: `RequestUserReviewDocumentation`
    - Window 3:
        - Method name: `ReceivePublishedDocumentation`

3. Select a process id to be used with all methods. Example: processId = "100"
4. Execute different methods in the following order:
    1. `RequestUserReviewDocumentation` with Request Data:
        ```json
        {
            "processId": "100"
        }
        ```
        This will subscribe to any request for review done for the specific process id and a response will be received when the process emits a notification. 
        Set timeout to 30 seconds. 

    2. `UserRequestFeatureDocumentation` with Request Data:
        ```json
        {
            "title": "some product title",
            "userDescription": "some user description",
            "content": "some product content",
            "processId": "100",
        }
        ```
        This request will kickstart the creation of a new process with the specific processId passing an initial event to the SK process.

5. Once the `RequestUserReviewDocumentation` is received, execute the following methods:
    1. `ReceivePublishedDocumentation` with Request Data:
        ```json
        {
            "processId": "100"
        }
        ```
        This will subscribe to any request for review done for the specific process id and a response will be received when the process emits a notification. 
        Set timeout to 30 seconds. 

    2. `UserReviewedDocumentation` with Request Data:
        ```json
        {
            "documentationApproved": true,
            "reason": "",
            "processData": 
            {
                "processId": "100"
            }
        }
        ```

### Debugging

For debugging and be able to set breakpoints in different stages of the app, you can:

- Install the [Visual Studio Dapr Extension](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vs-dapr) and make use of it by making use of the `<root>\dotnet\dapr.yaml` file already in the repository.

or

- Set the `ProcessWithCloudEvents.Grpc` as startup app, run and attach the Visual Studio debugger:
```
dapr run --app-id processwithcloudevents-grpc --app-port 58640 --app-protocol http -- dotnet run --no-build
```