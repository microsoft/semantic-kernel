// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace SemanticKernel.IntegrationTests.TestSettings;

[SuppressMessage("Performance", "CA1812:Internal class that is apparently never instantiated",
    Justification = "Configuration classes are instantiated through IConfiguration.")]
internal sealed class OnnxConfiguration
{
    public string? ModelId { get; set; }
    public string? ModelPath { get; set; }
    public string? ServiceId { get; internal set; }
}
