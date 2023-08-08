// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace SemanticKernel.IntegrationTests.TestSettings;

/// <summary>
/// Represents the main settings part of parameters used for MultiConnector integration tests.
/// </summary>
[SuppressMessage("Performance", "CA1812:Internal class that is apparently never instantiated",
    Justification = "Configuration classes are instantiated through IConfiguration.")]
internal sealed class MultiConnectorConfiguration
{
    public string OobaboogaEndPoint { get; set; } = "http://localhost";

    public List<OobaboogaConnectorConfiguration> OobaboogaCompletions { get; set; } = new();
}
