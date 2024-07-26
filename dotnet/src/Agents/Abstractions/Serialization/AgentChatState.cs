// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Agents.Serialization;

/// <summary>
/// Captures the serialized state of an <see cref="AgentChat"/> along with relevant meta-data.
/// </summary>
internal sealed class AgentChatState
{
    /// <summary>
    /// Metadata to identify the <see cref="Agent"/> instances participating in an <see cref="AgentChat"/>.
    /// </summary>
    public IEnumerable<AgentParticipant> Participants { get; init; } = Array.Empty<AgentParticipant>();

    /// <summary>
    /// The serialized chat history.
    /// </summary>
    /// <remarks>
    /// Converter will serialize JSON string as JSON.
    /// </remarks>
    [JsonConverter(typeof(JsonChannelStateConverter))]
    public string History { get; init; } = string.Empty;

    /// <summary>
    /// The state of each <see cref="AgentChannel"/> active in an <see cref="AgentChat"/>.
    /// </summary>
    public IEnumerable<AgentChannelState> Channels { get; init; } = [];
}
