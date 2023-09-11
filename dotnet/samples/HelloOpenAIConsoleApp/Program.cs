// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using RepoUtils;

var prompt = "Hello AI, what can you do for me?";
Console.WriteLine(prompt);

IConfigurationRoot configRoot = new ConfigurationBuilder()
            .AddEnvironmentVariables()
            .AddUserSecrets<Env>()
            .Build();

var azureOpenAI = configRoot.GetSection("AzureOpenAI");
var openAI = configRoot.GetSection("OpenAI");
var azureDeploymentName = azureOpenAI.GetValue<string>("DeploymentName");
var azureEndpoint = azureOpenAI.GetValue<string>("Endpoint");
var azureApiKey = azureOpenAI.GetValue<string>("ApiKey");
var openaiModelId = openAI.GetValue<string>("ModelId");
var openaiApiKey = openAI.GetValue<string>("ApiKey");

IKernel kernel = new KernelBuilder()
            .WithAzureTextCompletionService(deploymentName: azureDeploymentName, endpoint: azureEndpoint, apiKey: azureApiKey, serviceId: "azure")
            .WithOpenAITextCompletionService(modelId: openaiModelId, apiKey: openaiApiKey, serviceId: "openai")
            .Build();

var result = await kernel.InvokeSemanticFunctionAsync("Hello AI, what can you do for me?", requestSettings: new { max_tokens = 16, temperature = 0.7, service_id = "azure" });
// var result = await kernel.InvokeSemanticFunctionAsync(prompt, requestSettings: new OpenAITextRequestSettings() { MaxTokens = 256, Temperature = 0.7 });

if (result.LastException is not null)
{
    Console.WriteLine(result.LastException.Message);
}

Console.WriteLine(result.Result);
