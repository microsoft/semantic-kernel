// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0130 // Namespace does not match folder structure
// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticKernel.Planning.Flow;
#pragma warning restore IDE0130 // Namespace does not match folder structure

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading.Tasks;
using AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Memory;

public class FlowStatusProvider : IFlowStatusProvider
{
    private readonly IMemoryStore _memoryStore;

    private readonly string _collectionName;

    public FlowStatusProvider(IMemoryStore memoryStore, string? collectionName = null)
    {
        this._memoryStore = memoryStore;
        this._collectionName = collectionName ?? nameof(FlowStatusProvider);

        if (!this._memoryStore.DoesCollectionExistAsync(this._collectionName).Result)
        {
            Task.Run(async () => await this._memoryStore.CreateCollectionAsync(this._collectionName).ConfigureAwait(false));
        }
    }

    public async Task<Dictionary<string, string>> GetVariables(string sessionId)
    {
        var result = await (this._memoryStore.GetAsync(this._collectionName, this.GetFlowStatusStorageKey(sessionId))).ConfigureAwait(false);
        var text = result?.Metadata.Text ?? string.Empty;

        if (!string.IsNullOrEmpty(text))
        {
            try
            {
                return JsonSerializer.Deserialize<Dictionary<string, string>>(text) ??
                       new Dictionary<string, string>();
            }
            catch
            {
                throw new InvalidOperationException(
                    $"Failed to deserialize flow status for session {sessionId}, data={text}");
            }
        }
        else
        {
            return new Dictionary<string, string>();
        }
    }

    public async Task SaveVariables(string sessionId, Dictionary<string, string> variables)
    {
        var json = JsonSerializer.Serialize(variables);
        await this._memoryStore.UpsertAsync(this._collectionName, this.CreateMemoryRecord(this.GetFlowStatusStorageKey(sessionId), json))
            .ConfigureAwait(false);
    }

    private string GetFlowStatusStorageKey(string sessionId)
    {
        return $"FlowStatus_{sessionId}";
    }

    public async Task<ChatHistory?> GetChatHistoryAsync(string sessionId, string stepId)
    {
        var result = await this._memoryStore.GetAsync(this._collectionName, this.GetChatHistoryStorageKey(sessionId, stepId)).ConfigureAwait(false);
        var text = result?.Metadata.Text ?? string.Empty;

        if (!string.IsNullOrEmpty(text))
        {
            try
            {
                return ChatHistorySerializer.Deserialize(text);
            }
            catch
            {
                throw new InvalidOperationException(
                    $"Failed to deserialize chat history for session {sessionId}, data={text}");
            }
        }
        else
        {
            return null;
        }
    }

    public async Task SaveChatHistoryAsync(string sessionId, string stepId, ChatHistory history)
    {
        var json = ChatHistorySerializer.Serialize(history);
        await this._memoryStore.UpsertAsync(this._collectionName, this.CreateMemoryRecord(this.GetChatHistoryStorageKey(sessionId, stepId), json))
            .ConfigureAwait(false);
    }

    private string GetChatHistoryStorageKey(string sessionId, string stepId)
    {
        return $"ChatHistory_{sessionId}_{stepId}";
    }

    public async Task<List<ReActStep>> GetReActStepsAsync(string sessionId, string stepId)
    {
        var result = await this._memoryStore.GetAsync(this._collectionName, this.GetStepsStorageKey(sessionId, stepId)).ConfigureAwait(false);
        var text = result?.Metadata.Text ?? string.Empty;

        if (!string.IsNullOrEmpty(text))
        {
            try
            {
                return JsonSerializer.Deserialize<List<ReActStep>>(text) ?? new List<ReActStep>();
            }
            catch
            {
                throw new InvalidOperationException(
                    $"Failed to deserialize steps for session {sessionId}, data={text}");
            }
        }

        return new List<ReActStep>();
    }

    public async Task SaveReActStepsAsync(string sessionId, string stepId, List<ReActStep> steps)
    {
        var json = JsonSerializer.Serialize(steps);
        await this._memoryStore.UpsertAsync(this._collectionName, this.CreateMemoryRecord(this.GetStepsStorageKey(sessionId, stepId), json))
            .ConfigureAwait(false);
    }

    private string GetStepsStorageKey(string sessionId, string stepId)
    {
        // TODO: handle potential steps with multiple goals
        return $"Steps_{sessionId}_{stepId}";
    }

    private MemoryRecord CreateMemoryRecord(string key, string text)
    {
        return MemoryRecord.LocalRecord(key, text, null, Embedding<float>.Empty);
    }
}
