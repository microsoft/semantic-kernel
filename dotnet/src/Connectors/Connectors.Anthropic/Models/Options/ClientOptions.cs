// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.Anthropic;

/// <summary>
/// Represents the options for configuring the Anthropic client.
/// </summary>
public abstract class ClientOptions
{
    internal string Version { get; init; }

    /// <summary>
    /// Represents the options for configuring the Anthropic client.
    /// </summary>
    internal protected ClientOptions(string version)
    {
        this.Version = version;
    }
}
