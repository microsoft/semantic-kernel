// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Agents.Internal;

/// <summary>
/// Tracks channel along with its hashed key.
/// </summary>
internal readonly struct ChannelReference
{
    /// <summary>
    /// The referenced channel.
    /// </summary>
    public AgentChannel Channel { get; }

    /// <summary>
    /// The channel hash.
    /// </summary>
    public string Hash { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="ChannelReference"/> class.
    /// </summary>
    public ChannelReference(AgentChannel channel, string hash)
    {
        this.Channel = channel;
        this.Hash = hash;
    }
}
