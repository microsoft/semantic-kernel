// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextCompletion;
using Microsoft.SemanticKernel.SemanticFunctions;
using RepoUtils;

#pragma warning disable RCS1036 // Remove unnecessary blank line.

var prompt = "Hello AI, what can you do for me?";
Console.WriteLine(prompt);

IConfigurationRoot configRoot = new ConfigurationBuilder()
            .AddEnvironmentVariables()
            .AddUserSecrets<Env>()
            .Build();

var azureOpenAI = configRoot.GetSection("AzureOpenAI");
var openAI = configRoot.GetSection("OpenAI");
var azureDeploymentName = azureOpenAI.GetValue<string>("DeploymentName")!;
var azureEndpoint = azureOpenAI.GetValue<string>("Endpoint")!;
var azureApiKey = azureOpenAI.GetValue<string>("ApiKey")!;
var openaiModelId = openAI.GetValue<string>("ModelId")!;
var openaiApiKey = openAI.GetValue<string>("ApiKey")!;

IKernel kernel = new KernelBuilder()
            .WithOpenAITextCompletionService(modelId: openaiModelId, apiKey: openaiApiKey, serviceId: "openai")
            .WithAzureTextCompletionService(deploymentName: azureDeploymentName, endpoint: azureEndpoint, apiKey: azureApiKey, serviceId: "azure")
            .Build();



// Option 1: Use AnonymousType for request settings
var result = await kernel.InvokeSemanticFunctionAsync("Hello AI, what can you do for me?", requestSettings: new { MaxTokens = 16, Temperature = 0.7, ServiceId = "azure" });

Console.WriteLine(result.LastException is not null ? result.LastException.Message : result.Result);




// Option 2: Use OpenAI specific request settings
result = await kernel.InvokeSemanticFunctionAsync(prompt, requestSettings: new OpenAITextRequestSettings() { MaxTokens = 256, Temperature = 0.7, ServiceId = "azure" });

Console.WriteLine(result.LastException is not null ? result.LastException.Message : result.Result);



// Option 3: Load request settings 
string configPayload = @"{
          ""schema"": 1,
          ""description"": ""Say hello to an AI"",
          ""type"": ""completion"",
          ""completion"": {
            ""service_id"": ""azure"",
            ""max_tokens"": 60,
            ""temperature"": 0.5,
            ""top_p"": 0.0,
            ""presence_penalty"": 0.0,
            ""frequency_penalty"": 0.0
          }
        }";
var templateConfig = JsonSerializer.Deserialize<PromptTemplateConfig>(configPayload);

var func = kernel.CreateSemanticFunction(prompt, config: templateConfig!, "HelloAI");

result = await kernel.RunAsync(func);

Console.WriteLine(result.LastException is not null ? result.LastException.Message : result.Result);
