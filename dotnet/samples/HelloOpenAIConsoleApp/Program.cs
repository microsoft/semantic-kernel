// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using RepoUtils;

Console.WriteLine("Hello AI, what can you do for me?");

IConfigurationRoot configRoot = new ConfigurationBuilder()
            .AddEnvironmentVariables()
            .AddUserSecrets<Env>()
            .Build();

var section = configRoot.GetSection("AzureOpenAI");
var deploymentName = section.GetValue<string>("DeploymentName");
var endpoint = section.GetValue<string>("Endpoint");
var apiKey = section.GetValue<string>("ApiKey");

IKernel kernel = new KernelBuilder()
            .WithAzureTextCompletionService(deploymentName, endpoint, apiKey)
            .Build();

var result = await kernel.InvokeSemanticFunctionAsync("Hello AI, what can you do for me?");

if (result.LastException is not null)
{
    Console.WriteLine(result.LastException.Message);
}

Console.WriteLine(result.Result);
