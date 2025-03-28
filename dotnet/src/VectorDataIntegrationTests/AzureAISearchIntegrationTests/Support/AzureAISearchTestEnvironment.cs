// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;

namespace AzureAISearchIntegrationTests.Support;

#pragma warning disable CA1810 // Initialize all static fields when those fields are declared

internal static class AzureAISearchTestEnvironment
{
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
