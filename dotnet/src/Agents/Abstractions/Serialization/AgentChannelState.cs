// Copyright (c) Microsoft. All rights reserved.
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Agents.Serialization;

/// <summary>
/// %%%
/// </summary>
internal sealed class AgentChannelState
{
    /// <summary>
    /// %%%
    /// </summary>
    public string ChannelKey { get; set; } = string.Empty;

    /// <summary>
    /// %%%
    /// </summary>
    public string ChannelType { get; set; } = string.Empty;

    /// <summary>
    /// %%%
    /// </summary>
    [JsonConverter(typeof(JsonChannelStateConverter))]
    public string ChannelState { get; set; } = string.Empty;
}
