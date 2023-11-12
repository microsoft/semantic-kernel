// Copyright (c) Microsoft. All rights reserved.

using System.Reflection;
using Microsoft.Extensions.Configuration;

namespace SemanticKernel.Experimental.Assistants.UnitTests;

internal static class TestConfig
{
    public static IConfiguration Configuration { get; } = CreateConfiguration();

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
