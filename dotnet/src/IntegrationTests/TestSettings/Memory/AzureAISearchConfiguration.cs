// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace SemanticKernel.IntegrationTests.TestSettings.Memory;

[SuppressMessage("Design", "CA1054:URI-like parameters should not be strings", Justification = "This is just for test configuration")]
public sealed class AzureAISearchConfiguration(string serviceUrl, string apiKey)
{
    [SuppressMessage("Design", "CA1056:URI-like properties should not be strings", Justification = "This is just for test configuration")]
    public string ServiceUrl { get; set; } = serviceUrl;

    public string ApiKey { get; set; } = apiKey;
}
