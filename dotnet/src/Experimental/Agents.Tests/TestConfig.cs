// Copyright (c) Microsoft. All rights reserved.

using System.Reflection;
using Microsoft.Extensions.Configuration;
using Xunit.Sdk;

namespace SemanticKernel.Experimental.Agents.Tests;

internal static class TestConfig
{
    public static IConfiguration Configuration { get; } = CreateConfiguration();

    public static string AzureOpenAIEndpoint =>
        Configuration.GetValue<string>("AzureOpenAIEndpoint") ??
        throw new TestClassException("Missing Azure OpenAI Endpoint.");

    public static string AzureOpenAIAPIKey =>
        Configuration.GetValue<string>("AzureOpenAIAPIKey") ??
        throw new TestClassException("Missing Azure OpenAI API Key.");
    public static string AzureOpenAIDeploymentName =>
        Configuration.GetValue<string>("AzureOpenAIDeploymentName") ??
        throw new TestClassException("Missing Azure OpenAI deployment name.");

    private static IConfiguration CreateConfiguration()
    {
        return
            new ConfigurationBuilder()
                .AddEnvironmentVariables()
                .AddJsonFile("testsettings.json")
                .AddJsonFile("testsettings.development.json", optional: true)
                .AddUserSecrets(Assembly.GetExecutingAssembly())
                .Build();
    }
}
