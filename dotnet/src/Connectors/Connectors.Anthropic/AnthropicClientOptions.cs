// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.Anthropic;

#pragma warning disable CA1707 // Identifiers should not contain underscores
#pragma warning disable CA1008 // Enums should have zero value

/// <summary>
/// Represents the options for configuring the Anthropic client.
/// </summary>
public abstract class ClientOptions
{
    internal string Version { get; private protected init; } = null!;
}

/// <summary>
/// Represents the options for configuring the Anthropic client with Anthropic provider.
/// </summary>
public sealed class AnthropicClientOptions : ClientOptions
{
    private const ServiceVersion LatestVersion = ServiceVersion.V2023_06_01;

    /// <summary> The version of the service to use. </summary>
    public enum ServiceVersion
    {
        /// <summary> Service version "2023-01-01". </summary>
        V2023_01_01 = 0,

        /// <summary> Service version "2023-06-01". </summary>
        V2023_06_01 = 1,
    }

    /// <summary>
    /// Initializes new instance of <see cref="AnthropicClientOptions"/>
    /// </summary>
    /// <param name="version">
    /// This parameter is optional.
    /// Default value is <see cref="AnthropicClientOptions.LatestVersion"/>.<br/>
    /// </param>
    /// <exception cref="NotSupportedException">Provided version is not supported.</exception>
    public AnthropicClientOptions(ServiceVersion version = LatestVersion)
    {
        this.Version = version switch
        {
            ServiceVersion.V2023_01_01 => "2023-01-01",
            ServiceVersion.V2023_06_01 => "2023-06-01",
            _ => throw new ArgumentOutOfRangeException(version.ToString())
        };
    }
}

/// <summary>
/// Represents the options for configuring the Anthropic client with Google VertexAI provider.
/// </summary>
public sealed class VertexAIAnthropicClientOptions : ClientOptions
{
    private const ServiceVersion LatestVersion = ServiceVersion.V2023_10_16;

    /// <summary> The version of the service to use. </summary>
    public enum ServiceVersion
    {
        /// <summary> Service version "vertex-2023-10-16". </summary>
        V2023_10_16 = 0,
    }

    /// <summary>
    /// Initializes new instance of <see cref="VertexAIAnthropicClientOptions"/>
    /// </summary>
    /// <param name="version">
    /// This parameter is optional.
    /// Default value is <see cref="VertexAIAnthropicClientOptions.LatestVersion"/>.<br/>
    /// </param>
    /// <exception cref="NotSupportedException">Provided version is not supported.</exception>
    public VertexAIAnthropicClientOptions(ServiceVersion version = LatestVersion)
    {
        this.Version = version switch
        {
            ServiceVersion.V2023_10_16 => "vertex-2023-10-16",
            _ => throw new ArgumentOutOfRangeException(version.ToString())
        };
    }
}

/// <summary>
/// Represents the options for configuring the Anthropic client with Amazon Bedrock provider.
/// </summary>
public sealed class AmazonBedrockAnthropicClientOptions : ClientOptions
{
    private const ServiceVersion LatestVersion = ServiceVersion.V2023_05_31;

    /// <summary> The version of the service to use. </summary>
    public enum ServiceVersion
    {
        /// <summary> Service version "bedrock-2023-05-31". </summary>
        V2023_05_31 = 0,
    }

    /// <summary>
    /// Initializes new instance of <see cref="AmazonBedrockAnthropicClientOptions"/>
    /// </summary>
    /// <param name="version">
    /// This parameter is optional.
    /// Default value is <see cref="AmazonBedrockAnthropicClientOptions.LatestVersion"/>.<br/>
    /// </param>
    /// <exception cref="NotSupportedException">Provided version is not supported.</exception>
    public AmazonBedrockAnthropicClientOptions(ServiceVersion version = LatestVersion)
    {
        this.Version = version switch
        {
            ServiceVersion.V2023_05_31 => "bedrock-2023-05-31",
            _ => throw new ArgumentOutOfRangeException(version.ToString())
        };
    }
}
