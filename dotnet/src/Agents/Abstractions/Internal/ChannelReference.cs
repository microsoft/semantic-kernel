// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Agents.Internal;

/// <summary>
/// Tracks channel along with its hashed key.
/// </summary>
internal readonly struct ChannelReference(AgentChannel channel, string hash)
{
    /// <summary>
    /// The referenced channel.
    /// </summary>
    public AgentChannel Channel { get; } = channel;

    /// <summary>
    /// The channel hash.
    /// </summary>
    public string Hash { get; } = hash;
}
