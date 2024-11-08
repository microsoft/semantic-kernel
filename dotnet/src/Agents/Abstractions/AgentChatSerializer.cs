// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.Serialization;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Able to serialize and deserialize an <see cref="AgentChat"/>.
/// </summary>
public sealed class AgentChatSerializer
{
    private readonly AgentChatState _state;

    private static readonly JsonSerializerOptions s_defaultOptions =
        new()
        {
            WriteIndented = true,
            DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingDefault,
        };

    /// <summary>
    /// Serialize the provided <see cref="AgentChat"/> to the target stream.
    /// </summary>
    public static async Task SerializeAsync<TChat>(TChat chat, Stream stream, JsonSerializerOptions? serializerOptions = null) where TChat : AgentChat
    {
        AgentChatState state = chat.Serialize();
        await JsonSerializer.SerializeAsync(stream, state, serializerOptions ?? s_defaultOptions).ConfigureAwait(false);
    }

    /// <summary>
    /// Provides a <see cref="AgentChatSerializer"/> that is able to restore an <see cref="AgentChat"/>.
    /// </summary>
    public static async Task<AgentChatSerializer> DeserializeAsync(Stream stream, JsonSerializerOptions? serializerOptions = null)
    {
        AgentChatState state =
            await JsonSerializer.DeserializeAsync<AgentChatState>(stream, serializerOptions ?? s_defaultOptions).ConfigureAwait(false) ??
            throw new KernelException("Unable to restore chat: invalid format.");

        return new AgentChatSerializer(state);
    }

    /// <summary>
    /// Enumerates the participants of the original <see cref="AgentChat"/> so that
    /// the caller may be include them in the restored <see cref="AgentChat"/>.
    /// </summary>
    public IEnumerable<AgentParticipant> Participants => this._state.Participants;

    /// <summary>
    /// Restore the <see cref="AgentChat"/> to the previously captured state.
    /// </summary>
    public Task DeserializeAsync<TChat>(TChat chat) where TChat : AgentChat => chat.DeserializeAsync(this._state);

    private AgentChatSerializer(AgentChatState state)
    {
        this._state = state;
    }
}
