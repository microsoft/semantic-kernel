// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Experimental.Orchestration.Abstractions;
using Microsoft.SemanticKernel.Experimental.Orchestration.FlowExecutor;
using Microsoft.SemanticKernel.Memory;

#pragma warning disable IDE0130
namespace Microsoft.SemanticKernel.Experimental.Orchestration;
#pragma warning restore IDE0130

/// <summary>
/// Default flow status provider implemented on top of <see cref="IMemoryStore"/>
/// </summary>
public class FlowStatusProvider : IFlowStatusProvider
{
    private readonly IMemoryStore _memoryStore;

    private readonly string _collectionName;

    /// <summary>
    /// Initializes a new instance of the <see cref="FlowStatusProvider"/> class.
    /// </summary>
    /// <param name="memoryStore"><see cref="IMemoryStore"/> instance</param>
    /// <param name="collectionName">Collection name in <see cref="IMemoryStore"/> instance</param>
    public FlowStatusProvider(IMemoryStore memoryStore, string? collectionName = null)
    {
        this._memoryStore = memoryStore;
        this._collectionName = collectionName ?? nameof(FlowStatusProvider);

        Task.Run(async () =>
        {
            if (!await this._memoryStore.DoesCollectionExistAsync(this._collectionName).ConfigureAwait(false))
            {
                await this._memoryStore.CreateCollectionAsync(this._collectionName).ConfigureAwait(false);
            }
        }).GetAwaiter().GetResult();
    }

    /// <inheritdoc/>
    public async Task<ExecutionState> GetExecutionStateAsync(string sessionId)
    {
        var result = await (this._memoryStore.GetAsync(this._collectionName, this.GetExecutionStateStorageKey(sessionId))).ConfigureAwait(false);
        var text = result?.Metadata.Text ?? string.Empty;

        if (!string.IsNullOrEmpty(text))
        {
            try
            {
                return JsonSerializer.Deserialize<ExecutionState>(text) ?? new ExecutionState();
            }
            catch
            {
                throw new InvalidOperationException(
                    $"Failed to deserialize execution state for sessionId={sessionId}, data={text}");
            }
        }
        else
        {
            return new ExecutionState();
        }
    }

    /// <inheritdoc/>
    public async Task SaveExecutionStateAsync(string sessionId, ExecutionState state)
    {
        var json = JsonSerializer.Serialize(state);
        await this._memoryStore.UpsertAsync(this._collectionName, this.CreateMemoryRecord(this.GetExecutionStateStorageKey(sessionId), json))
            .ConfigureAwait(false);
    }

    private string GetExecutionStateStorageKey(string sessionId)
    {
        return $"FlowStatus_{sessionId}";
    }

    /// <inheritdoc/>
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

    /// <inheritdoc/>
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

    /// <inheritdoc/>
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

    /// <inheritdoc/>
    public async Task SaveReActStepsAsync(string sessionId, string stepId, List<ReActStep> steps)
    {
        var json = JsonSerializer.Serialize(steps);
        await this._memoryStore.UpsertAsync(this._collectionName, this.CreateMemoryRecord(this.GetStepsStorageKey(sessionId, stepId), json))
            .ConfigureAwait(false);
    }

    private string GetStepsStorageKey(string sessionId, string stepId)
    {
        return $"Steps_{sessionId}_{stepId}";
    }

    private MemoryRecord CreateMemoryRecord(string key, string text)
    {
        return MemoryRecord.LocalRecord(key, text, null, ReadOnlyMemory<float>.Empty);
    }
}
