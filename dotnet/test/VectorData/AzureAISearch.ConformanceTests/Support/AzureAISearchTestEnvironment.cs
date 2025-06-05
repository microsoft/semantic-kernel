// Copyright (c) Microsoft. All rights reserved.

using System.Text.RegularExpressions;
using Microsoft.Extensions.Configuration;

namespace AzureAISearch.ConformanceTests.Support;

#pragma warning disable CA1810 // Initialize all static fields when those fields are declared

internal static class AzureAISearchTestEnvironment
{
#pragma warning disable CA1308 // Normalize strings to uppercase
    public static readonly string TestIndexPostfix = new Regex("[^a-zA-Z0-9]").Replace(Environment.MachineName.ToLowerInvariant(), "");
#pragma warning restore CA1308 // Normalize strings to uppercase

    public static readonly string? ServiceUrl, ApiKey;

    public static bool IsConnectionInfoDefined => ServiceUrl is not null;

    static AzureAISearchTestEnvironment()
    {
        var configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<AzureAISearchUrlRequiredAttribute>()
            .Build();

        var azureAISearchSection = configuration.GetSection("AzureAISearch");
        ServiceUrl = azureAISearchSection?["ServiceUrl"];
        ApiKey = azureAISearchSection?["ApiKey"];
    }
}
