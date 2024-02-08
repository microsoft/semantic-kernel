// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;

namespace HomeAutomation;

/// <summary>
/// Loads configuration upon instanciation.
/// </summary>
internal sealed class AppConfiguration
{
    internal string AzureOpenAiDeployment { get; set; }
    internal string AzureOpenAiEndpoint { get; set; }
    internal string AzureOpenAiApiKey { get; set; }

    public AppConfiguration(IConfiguration config)
    {
        AzureOpenAiDeployment = config["AzureOpenAiDeployment"] ?? throw new ArgumentNullException(nameof(AzureOpenAiDeployment));
        AzureOpenAiEndpoint = config["AzureOpenAiEndpoint"] ?? throw new ArgumentNullException(nameof(AzureOpenAiEndpoint));
        AzureOpenAiApiKey = config["AzureOpenAiApiKey"] ?? throw new ArgumentNullException(nameof(AzureOpenAiApiKey));
    }
}
