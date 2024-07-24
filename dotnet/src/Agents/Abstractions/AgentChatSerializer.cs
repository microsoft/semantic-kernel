// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// %%%
/// </summary>
public static class AgentChatSerializer
{
    /// <summary>
    /// %%%
    /// </summary>
    public static readonly JsonSerializerOptions DefaultOptions =
        new()
        {
            WriteIndented = true,
            DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingDefault,
        };

    /// <summary>
    /// %%%
    /// </summary>
    public static async Task SerializeAsync<TChat>(TChat chat, Stream stream) where TChat : AgentChat
    {
        AgentChatState state = chat.Serialize();
        await JsonSerializer.SerializeAsync(stream, state, DefaultOptions).ConfigureAwait(false);
    }

    /// <summary>
    /// %%%
    /// </summary>
    public static async Task DeserializeAsync<TChat>(TChat chat, Stream stream) where TChat : AgentChat
    {
        AgentChatState state =
            await JsonSerializer.DeserializeAsync<AgentChatState>(stream, DefaultOptions).ConfigureAwait(false) ??
            throw new KernelException("%%%");

        await chat.DeserializeAsync(state).ConfigureAwait(false);
    }
}

/// <summary>
/// %%%
/// </summary>
internal sealed class AgentChatState
{
    /// <summary>
    /// %%%
    /// </summary>
    public ChatHistory History { get; set; } = [];

    /// <summary>
    /// %%%
    /// </summary>
    public IEnumerable<AgentChannelState> Channels { get; set; } = [];
}

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
    public string JsonState { get; set; } = string.Empty;
}
