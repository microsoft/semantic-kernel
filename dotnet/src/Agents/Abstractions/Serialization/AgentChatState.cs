// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Agents.Serialization;

/// <summary>
/// %%%
/// </summary>
internal sealed class AgentChatState
{
    /// <summary>
    /// %%%
    /// </summary>
    public IEnumerable<AgentParticipant> Participants { get; init; } = Array.Empty<AgentParticipant>();

    /// <summary>
    /// %%%
    /// </summary>
    [JsonConverter(typeof(JsonChannelStateConverter))]
    public string History { get; init; } = string.Empty;

    /// <summary>
    /// %%%
    /// </summary>
    public IEnumerable<AgentChannelState> Channels { get; init; } = [];
}
