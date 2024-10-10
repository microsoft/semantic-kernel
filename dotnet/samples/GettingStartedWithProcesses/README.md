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
[Step03_FoodPreparation](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/GettingStartedWithProcesses/Step03/Step03_FoodPreparation.cs)|Showcasing reuse of steps, creation of processes, spawning of multiple events.

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

### Step03_FoodPreparation

This tutorial contains a set of food recipes associated with the Food Preparation Processes of a restaurant.

The following recipes for preparation of Order Items are defined as SK Processes:

#### Product Preparation Processes

##### Potato Fries Preparation Process

``` mermaid
flowchart LR
    PreparePotatoFriesEvent([Prepare Potato <br/> Fries Event])
    PotatoFriesReadyEvent([Potato Fries <br/> Ready Event])

    GatherIngredientsStep[Gather Ingredients <br/> Step]
    CutStep[Cut Food <br/> Step]
    FryStep[Fry Food <br/> Step]

    PreparePotatoFriesEvent --> GatherIngredientsStep -->| Slice Potatoes <br/> _Ingredients Gathered_ | CutStep --> |**Potato Sliced Ready** <br/> _Food Sliced Ready_ | FryStep --> |_Fried Food Ready_|PotatoFriesReadyEvent
    FryStep -->|Fried Potato Ruined <br/> _Fried Food Ruined_| GatherIngredientsStep
```

##### Fried Fish Preparation Process

``` mermaid
flowchart LR
    PrepareFriedFishEvent([Prepare Fried <br/> Fish Event])
    FriedFishReadyEvent([Fried Fish <br/> Ready Event])

    GatherIngredientsStep[Gather Ingredients <br/> Step]
    CutStep[Cut Food <br/> Step]
    FryStep[Fry Food <br/> Step]

    PrepareFriedFishEvent --> GatherIngredientsStep -->| Chop Fish <br/> _Ingredients Gathered_ | CutStep --> |**Fish Chopped Ready** <br/> _Food Chopped Ready_| FryStep --> |_Fried Food Ready_ | FriedFishReadyEvent
    FryStep -->|**Fried Fish Ruined** <br/> _Fried Food Ruined_| GatherIngredientsStep
```

##### Fish Sandwich Preparation Process

``` mermaid
flowchart LR
    PrepareFishSandwichEvent([Prepare Fish <br/> Sandwich Event])
    FishSandwichReadyEvent([Fish Sandwich <br/> Ready Event])

    FriedFishStep[[Fried Fish <br/> Process Step]]
    AddBunsStep[Add Buns <br/> Step]
    AddSpecialSauceStep[Add Special <br/> Sauce Step]

    PrepareFishSandwichEvent -->|Prepare Fried Fish| FriedFishStep -->|Fried Fish Ready| AddBunsStep --> |Buns Added  | AddSpecialSauceStep --> |Special Sauce Added | FishSandwichReadyEvent
```

##### Fish And Chips Preparation Process

``` mermaid
flowchart LR
    PrepareFishAndChipsEvent([Prepare <br/> Fish And Chips <br/> Event])
    FishAndChipsReadyEvent([Fish And Chips <br/> Ready Event])

    FriedFishStep[[Fried Fish <br/> Process Step]]
    PotatoFriesStep[[Potato Fries  <br/> Process Step]]
    AddCondiments[Add Condiments <br/> Step ]

    PrepareFishAndChipsEvent -->|Prepare Fried Fish| FriedFishStep --> |Fried Fish Ready| AddCondiments
    PrepareFishAndChipsEvent -->|Prepare Potato Fries| PotatoFriesStep -->|Potato Fries Ready| AddCondiments
    AddCondiments -->|Condiments Added| FishAndChipsReadyEvent
```

#### Single Order Preparation Process

Now with the existing product preparation processes, they can be used to create an even more complex process that can decide what product order to dispatch.

```mermaid
graph TD
    PrepareSingleOrderEvent([Prepare Single Order <br/> Event])
    SingleOrderReadyEvent([Single Order <br/> Ready Event])
    OrderPackedEvent([Order Packed <br/> Event])

    DispatchOrderStep{{Dispatch <br/> Order Step}}
    FriedFishStep[[Fried Fish  <br/> Process Step]]
    PotatoFriesStep[[Potato Fries <br/> Process Step]]
    FishSandwichStep[[Fish Sandwich <br/> Process Step]]
    FishAndChipsStep[[Fish & Chips <br/> Process Step]]

    PackFoodStep[Pack Food <br/> Step]

    PrepareSingleOrderEvent -->|Order Received| DispatchOrderStep
    DispatchOrderStep -->|Prepare Fried Fish| FriedFishStep -->|Fried Fish Ready| SingleOrderReadyEvent
    DispatchOrderStep -->|Prepare Potato Fries| PotatoFriesStep -->|Potato Fries Ready| SingleOrderReadyEvent
    DispatchOrderStep -->|Prepare Fish Sandwich| FishSandwichStep -->|Fish Sandwich Ready| SingleOrderReadyEvent
    DispatchOrderStep -->|Prepare Fish & Chips| FishAndChipsStep -->|Fish & Chips Ready| SingleOrderReadyEvent

    SingleOrderReadyEvent-->PackFoodStep --> OrderPackedEvent
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
