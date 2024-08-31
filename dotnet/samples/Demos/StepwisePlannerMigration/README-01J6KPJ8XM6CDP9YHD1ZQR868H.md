---
runme:
  document:
    relativePath: README.md
  session:
    id: 01J6KPJ8XM6CDP9YHD1ZQR868H
    updated: 2024-08-31 07:51:48Z
---

# Function Calling Stepwise Planner Migration

This demo application shows how to migrate from FunctionCallingStepwisePlanner to a new recommended approach for planning capability - Auto Function Calling.
The new approach produces the results more reliably and uses fewer tokens compared to FunctionCallingStepwisePlanner.

## Prerequisites

1. [OpenAI](ht*****************************************on) subscription.
2. Update `appsettings.Development.json` file with your configuration for `OpenAI` section or use .NET [Secret Manager](ht**************************************************************ts) (recommended approach):

```powershell {"id":"01J6KPP8817MRGF0PJPNK0EJYV"}
# OpenAI
# Make sure to use the model which supports function calling capability.
# Supported models: ht*********************************************************************ls
dotnet user-secrets set "OpenAI:ChatModelId" "... your model ..."
dotnet user-secrets set "OpenAI:ApiKey" "... your api key ... "
```

## Testing

1. Start ASP.NET Web API application.
2. Open `StepwisePlannerMigration.http` file and run listed requests.

It's possible to send [HTTP re****ts](ht*****************************************************************************.0) directly from `StepwisePlannerMigration.http` with Visual Studio 2022 version 17.8 or later. For Visual Studio Code users, use `StepwisePlannerMigration.http` file as REST API specification and use tool of your choice to send described requests.

## Migration guide

### Plan generation

Old approach:

```csharp {"id":"01J6KPP8817MRGF0PJPNZBEMRQ"}
Kernel kernel = Kernel
    .CreateBuilder()
    .Ad*******************on("gpt-4", Environment.GetEnvironmentVariable("OpenAI__ApiKey"))
    .Build();

FunctionCallingStepwisePlanner planner = new();

FunctionCallingStepwisePlannerResult result = await planner.ExecuteAsync(kernel, "Check current UTC time and return current weather in Boston city.");

ChatHistory generatedPlan = result.ChatHistory;
```

New approach:

```csharp {"id":"01J6KPP8817MRGF0PJPP5B628G"}
Kernel kernel = Kernel
    .CreateBuilder()
    .Ad*******************on("gpt-4", Environment.GetEnvironmentVariable("OpenAI__ApiKey"))
    .Build();

IChatCompletionService chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

ChatHistory chatHistory = [];
chatHistory.AddUserMessage("Check current UTC time and return current weather in Boston city.");

OpenAIPromptExecutionSettings executionSettings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

await chatCompletionService.GetChatMessageContentAsync(chatHistory, executionSettings, kernel);

ChatHistory generatedPlan = chatHistory;
```

### New plan execution

Old approach:

```csharp {"id":"01J6KPP8817MRGF0PJPRF33C92"}
Kernel kernel = Kernel
    .CreateBuilder()
    .Ad*******************on("gpt-4", Environment.GetEnvironmentVariable("OpenAI__ApiKey"))
    .Build();

FunctionCallingStepwisePlanner planner = new();

FunctionCallingStepwisePlannerResult result = await planner.ExecuteAsync(kernel, "Check current UTC time and return current weather in Boston city.");

string planResult = result.FinalAnswer;
```

New approach:

```csharp {"id":"01J6KPP8817MRGF0PJPSDD8X8X"}
Kernel kernel = Kernel
    .CreateBuilder()
    .Ad*******************on("gpt-4", Environment.GetEnvironmentVariable("OpenAI__ApiKey"))
    .Build();

OpenAIPromptExecutionSettings executionSettings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

FunctionResult result = await kernel.InvokePromptAsync("Check current UTC time and return current weather in Boston city.", new(executionSettings));

string planResult = result.ToString();
```

### Existing plan execution

Old approach:

```csharp {"id":"01J6KPP8817MRGF0PJPWK0KXNV"}
Kernel kernel = Kernel
    .CreateBuilder()
    .Ad*******************on("gpt-4", Environment.GetEnvironmentVariable("OpenAI__ApiKey"))
    .Build();

FunctionCallingStepwisePlanner planner = new();
ChatHistory existingPlan = GetExistingPlan(); // plan can be stored in database for reusability.

FunctionCallingStepwisePlannerResult result = await planner.ExecuteAsync(kernel, "Check current UTC time and return current weather in Boston city.", existingPlan);

string planResult = result.FinalAnswer;
```

New approach:

```csharp {"id":"01J6KPP8817MRGF0PJPYSS8F42"}
Kernel kernel = Kernel
    .CreateBuilder()
    .Ad*******************on("gpt-4", Environment.GetEnvironmentVariable("OpenAI__ApiKey"))
    .Build();

IChatCompletionService chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

ChatHistory existingPlan = GetExistingPlan(); // plan can be stored in database for reusability.

OpenAIPromptExecutionSettings executionSettings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

ChatMessageContent result = await chatCompletionService.GetChatMessageContentAsync(chatHistory, executionSettings, kernel);

string planResult = result.Content;
```
