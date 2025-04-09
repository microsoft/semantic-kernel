// Copyright (c) Microsoft. All rights reserved.
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Agents.Serialization;

/// <summary>
/// Captures the serialized state of an <see cref="AgentChannel"/> along with relevant meta-data.
/// </summary>
internal sealed class AgentChannelState
{
    /// <summary>
    /// The unique key for the channel.
    /// </summary>
    /// <remarks>
    /// This is a hash <see cref="AgentChat"/> generates and manages based <see cref="Agent.GetChannelKeys()"/>.
    /// </remarks>
    public string ChannelKey { get; set; } = string.Empty;

    /// <summary>
    /// The fully qualified type name of the channel.
    /// </summary>
    /// <remarks>
    /// Not utilized in deserialization, but useful for auditing the serialization payload.
    /// </remarks>
    public string ChannelType { get; set; } = string.Empty;

    /// <summary>
    /// The serialized channel state, as provided by <see cref="AgentChannel.Serialize"/>.
    /// </summary>
    /// <remarks>
    /// Converter will serialize JSON string as JSON.
    /// </remarks>
    [JsonConverter(typeof(JsonChannelStateConverter))]
    public string ChannelState { get; set; } = string.Empty;
}
