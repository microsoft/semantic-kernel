# Semantic Kernel Processes - Getting Started

This project contains a step by step guide to get started with  _Semantic Kernel Processes_.


#### NuGet:
- [Microsoft.SemanticKernel.Process.Abstractions](https://www.nuget.org/packages/Microsoft.SemanticKernel.Process.Abstractions)
- [Microsoft.SemanticKernel.Process.Core](https://www.nuget.org/packages/Microsoft.SemanticKernel.Process.Core)
- [Microsoft.SemanticKernel.Process.LocalRuntime](https://www.nuget.org/packages/Microsoft.SemanticKernel.Process.LocalRuntime)

#### Sources
- [Semantic Kernel Processes - Abstractions](https://github.com/microsoft/semantic-kernel/tree/main/dotnet/src/Experimental/Process.Abstractions)
- [Semantic Kernel Processes - Core](https://github.com/microsoft/semantic-kernel/tree/main/dotnet/src/Experimental/Process.Core)
- [Semantic Kernel Processes - LocalRuntime](https://github.com/microsoft/semantic-kernel/tree/main/dotnet/src/Experimental/Process.LocalRuntime)

The examples can be run as integration tests but their code can also be copied to stand-alone programs.

## Examples

The getting started with agents examples include:

Example|Description
---|---
[Step01_Processes](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/GettingStartedWithProcesses/Step01/Step01_Processes.cs)|How to create a simple process with a loop and a conditional exit
[Step02_AccountOpening](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/GettingStartedWithProcesses/Step02/Step02_AccountOpening.cs)|Showcasing processes cycles, fan in, fan out for opening an account.

### Step01_Processes

```mermaid
flowchart LR  
    Intro(Intro)--> UserInput(User Input)
    UserInput-->|User message == 'exit'| Exit(Exit)
    UserInput-->|User message| AssistantResponse(Assistant Response)
    AssistantResponse--> UserInput
```

### Step02_AccountOpening

```mermaid
flowchart LR  
    User(User) -->|Provides user details| FillForm(Fill New <br/> Customer <br/> Form)  

    FillForm -->|Need more info| AssistantMessage(Assistant <br/> Message)
    FillForm -->|Welcome Message| AssistantMessage
    FillForm --> CompletedForm((Completed Form))
    AssistantMessage --> User
  
    CompletedForm --> CreditCheck(Customer <br/> Credit Score <br/> Check)  
    CompletedForm --> Fraud(Fraud Detection)
    CompletedForm -->|New Customer Form + Conversation Transcript| CoreSystem
  
    CreditCheck -->|Failed - Notify user about insufficient credit score| Mailer(Mail <br/> Service)  
    CreditCheck -->|Approved| Fraud  
  
    Fraud --> |Failed - Notify user about failure to confirm user identity| Mailer  
    Fraud --> |Passed| CoreSystem(Core System <br/> Record <br/> Creation)  
  
    CoreSystem --> Marketing(New Marketing <br/> Record Creation)  
    CoreSystem --> CRM(CRM Record <br/> Creation)  
    CoreSystem -->|Account Details| Welcome(Welcome <br/> Packet)  
  
    Marketing -->|Success| Welcome  
    CRM -->|Success| Welcome  
  
    Welcome -->|Success: Notify User about Account Creation| Mailer  
    Mailer -->|End of Interaction| User
```


## Running Examples with Filters
Examples may be explored and ran within _Visual Studio_ using _Test Explorer_.

You can also run specific examples via the command-line by using test filters (`dotnet test --filter`). Type `dotnet test --help` at the command line for more details.

Example:

```
dotnet test --filter Step01_Processes
```

## Configuring Secrets

Each example requires secrets / credentials to access OpenAI or Azure OpenAI.

We suggest using .NET [Secret Manager](https://learn.microsoft.com/en-us/aspnet/core/security/app-secrets) to avoid the risk of leaking secrets into the repository, branches and pull requests. You can also use environment variables if you prefer.

To set your secrets with .NET Secret Manager:

1. Navigate the console to the project folder:

    ```
    cd dotnet/samples/GettingStartedWithProcesses
    ```

2. Examine existing secret definitions:

    ```
    dotnet user-secrets list
    ```

3. If needed, perform first time initialization:

    ```
    dotnet user-secrets init
    ```

4. Define secrets for either Open AI:

    ```
    dotnet user-secrets set "OpenAI:ChatModelId" "..."
    dotnet user-secrets set "OpenAI:ApiKey" "..."
    ```

5. Or Azure Open AI:

    ```
    dotnet user-secrets set "AzureOpenAI:DeploymentName" "..."
    dotnet user-secrets set "AzureOpenAI:ChatDeploymentName" "..."
    dotnet user-secrets set "AzureOpenAI:Endpoint" "https://... .openai.azure.com/"
    dotnet user-secrets set "AzureOpenAI:ApiKey" "..."
    ```

> NOTE: Azure secrets will take precedence, if both Open AI and Azure Open AI secrets are defined, unless `ForceOpenAI` is set:

```
protected override bool ForceOpenAI => true;
```
