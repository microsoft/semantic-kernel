// Copyright (c) Microsoft. All rights reserved.

using System.Reflection;
using Microsoft.Extensions.Configuration;
using Xunit.Sdk;

namespace SemanticKernel.Experimental.Agents.UnitTests;

internal static class TestConfig
{
    public const string SupportedGpt35TurboModel = "gpt-3.5-turbo-1106";

    public static IConfiguration Configuration { get; } = CreateConfiguration();

    public static string OpenAIApiKey =>
        TestConfig.Configuration.GetValue<string>("OpenAIApiKey") ??
        throw new TestClassException("Missing OpenAI APIKey.");

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
