// Copyright (c) Microsoft. All rights reserved.
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
    //public IEnumerable<ChatMessageContent> History { get; set; } = [];
    [JsonConverter(typeof(JsonChannelStateConverter))]
    public string History { get; set; } = string.Empty;

    /// <summary>
    /// %%%
    /// </summary>
    public IEnumerable<AgentChannelState> Channels { get; set; } = [];
}
