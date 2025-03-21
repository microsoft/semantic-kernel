// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace SemanticKernel.IntegrationTests.TestSettings;

[SuppressMessage("Performance", "CA1812:Internal class that is apparently never instantiated",
    Justification = "Configuration classes are instantiated through IConfiguration.")]
internal sealed class AzureAIConfiguration(string connectionString, string chatModelId)
{
    public string ConnectionString { get; set; } = connectionString;

    public string ChatModelId { get; set; } = chatModelId;
}
