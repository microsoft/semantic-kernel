// Copyright (c) Microsoft. All rights reserved.
using System.IO;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.Serialization;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// %%%
/// </summary>
public sealed class AgentChatSerializer
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
            await JsonSerializer.DeserializeAsync<AgentChatState>(stream).ConfigureAwait(false) ??
            throw new KernelException("%%%");

        await chat.DeserializeAsync(state).ConfigureAwait(false);
    }
}
