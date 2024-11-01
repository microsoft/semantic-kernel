# Function Calling Stepwise Planner Migration

This demo application shows how to migrate from FunctionCallingStepwisePlanner to a new recommended approach for planning capability - Auto Function Calling.
The new approach produces the results more reliably and uses fewer tokens compared to FunctionCallingStepwisePlanner.

## Prerequisites

1. [OpenAI](https://platform.openai.com/docs/introduction) subscription.
2. Update `appsettings.Development.json` file with your configuration for `OpenAI` section or use .NET [Secret Manager](https://learn.microsoft.com/en-us/aspnet/core/security/app-secrets) (recommended approach):

```powershell
# OpenAI
# Make sure to use the model which supports function calling capability.
# Supported models: https://platform.openai.com/docs/guides/function-calling/supported-models
dotnet user-secrets set "OpenAI:ChatModelId" "... your model ..."
dotnet user-secrets set "OpenAI:ApiKey" "... your api key ... "
```

## Testing

1. Start ASP.NET Web API application.
2. Open `StepwisePlannerMigration.http` file and run listed requests.

It's possible to send [HTTP requests](https://learn.microsoft.com/en-us/aspnet/core/test/http-files?view=aspnetcore-8.0) directly from `StepwisePlannerMigration.http` with Visual Studio 2022 version 17.8 or later. For Visual Studio Code users, use `StepwisePlannerMigration.http` file as REST API specification and use tool of your choice to send described requests.

## Migration guide

### Plan generation

Old approach:

```csharp
Kernel kernel = Kernel
    .CreateBuilder()
    .AddOpenAIChatCompletion("gpt-4", Environment.GetEnvironmentVariable("OpenAI__ApiKey"))
    .Build();

FunctionCallingStepwisePlanner planner = new();

FunctionCallingStepwisePlannerResult result = await planner.ExecuteAsync(kernel, "Check current UTC time and return current weather in Boston city.");

ChatHistory generatedPlan = result.ChatHistory;
```

New approach:

```csharp
Kernel kernel = Kernel
    .CreateBuilder()
    .AddOpenAIChatCompletion("gpt-4", Environment.GetEnvironmentVariable("OpenAI__ApiKey"))
    .Build();

IChatCompletionService chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

ChatHistory chatHistory = [];
chatHistory.AddUserMessage("Check current UTC time and return current weather in Boston city.");

OpenAIPromptExecutionSettings executionSettings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

await chatCompletionService.GetChatMessageContentAsync(chatHistory, executionSettings, kernel);

ChatHistory generatedPlan = chatHistory;
```

### New plan execution

Old approach:

```csharp
Kernel kernel = Kernel
    .CreateBuilder()
    .AddOpenAIChatCompletion("gpt-4", Environment.GetEnvironmentVariable("OpenAI__ApiKey"))
    .Build();

FunctionCallingStepwisePlanner planner = new();

FunctionCallingStepwisePlannerResult result = await planner.ExecuteAsync(kernel, "Check current UTC time and return current weather in Boston city.");

string planResult = result.FinalAnswer;
```

New approach:

```csharp
Kernel kernel = Kernel
    .CreateBuilder()
    .AddOpenAIChatCompletion("gpt-4", Environment.GetEnvironmentVariable("OpenAI__ApiKey"))
    .Build();

OpenAIPromptExecutionSettings executionSettings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

FunctionResult result = await kernel.InvokePromptAsync("Check current UTC time and return current weather in Boston city.", new(executionSettings));

string planResult = result.ToString();
```

### Existing plan execution

Old approach:

```csharp
Kernel kernel = Kernel
    .CreateBuilder()
    .AddOpenAIChatCompletion("gpt-4", Environment.GetEnvironmentVariable("OpenAI__ApiKey"))
    .Build();

FunctionCallingStepwisePlanner planner = new();
ChatHistory existingPlan = GetExistingPlan(); // plan can be stored in database for reusability.

FunctionCallingStepwisePlannerResult result = await planner.ExecuteAsync(kernel, "Check current UTC time and return current weather in Boston city.", existingPlan);

string planResult = result.FinalAnswer;
```

New approach:

```csharp
Kernel kernel = Kernel
    .CreateBuilder()
    .AddOpenAIChatCompletion("gpt-4", Environment.GetEnvironmentVariable("OpenAI__ApiKey"))
    .Build();

IChatCompletionService chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

ChatHistory existingPlan = GetExistingPlan(); // plan can be stored in database for reusability.

OpenAIPromptExecutionSettings executionSettings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

ChatMessageContent result = await chatCompletionService.GetChatMessageContentAsync(chatHistory, executionSettings, kernel);

string planResult = result.Content;
```
