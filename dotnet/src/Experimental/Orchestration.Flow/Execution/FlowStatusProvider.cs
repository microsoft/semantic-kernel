// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
using Microsoft.SemanticKernel.ChatCompletion;
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
using Microsoft.SemanticKernel.ChatCompletion;
=======
=======
>>>>>>> origin/main
=======
<<<<<<< main
using Microsoft.SemanticKernel.ChatCompletion;
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
using Microsoft.SemanticKernel.ChatCompletion;
=======
using Microsoft.SemanticKernel.AI.ChatCompletion;
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
using Microsoft.SemanticKernel.Experimental.Orchestration.Abstractions;
using Microsoft.SemanticKernel.Experimental.Orchestration.Execution;
using Microsoft.SemanticKernel.Memory;

<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
namespace Microsoft.SemanticKernel.Experimental.Orchestration;
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
namespace Microsoft.SemanticKernel.Experimental.Orchestration;
=======
=======
<<<<<<< HEAD
namespace Microsoft.SemanticKernel.Experimental.Orchestration;
=======
>>>>>>> origin/main
=======
<<<<<<< HEAD
namespace Microsoft.SemanticKernel.Experimental.Orchestration;
=======
>>>>>>> Stashed changes
#pragma warning disable IDE0130
namespace Microsoft.SemanticKernel.Experimental.Orchestration;
#pragma warning restore IDE0130
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes

/// <summary>
/// Default flow status provider implemented on top of <see cref="IMemoryStore"/>
/// </summary>
public sealed class FlowStatusProvider : IFlowStatusProvider
{
    private readonly IMemoryStore _memoryStore;

    private readonly string _collectionName;

    /// <summary>
    /// Initializes a new instance of the <see cref="FlowStatusProvider"/> class.
    /// </summary>
    public static async Task<FlowStatusProvider> ConnectAsync(IMemoryStore memoryStore, string? collectionName = null)
    {
        var provider = new FlowStatusProvider(memoryStore, collectionName);
        return await InitializeProviderStoreAsync(provider).ConfigureAwait(false);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="FlowStatusProvider"/> class.
    /// </summary>
    /// <param name="memoryStore"><see cref="IMemoryStore"/> instance</param>
    /// <param name="collectionName">Collection name in <see cref="IMemoryStore"/> instance</param>
    private FlowStatusProvider(IMemoryStore memoryStore, string? collectionName = null)
    {
        this._memoryStore = memoryStore;
        this._collectionName = collectionName ?? nameof(FlowStatusProvider);
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
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
                return JsonSerializer.Deserialize<List<ReActStep>>(text) ?? [];
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
                return JsonSerializer.Deserialize<List<ReActStep>>(text) ?? [];
=======
=======
>>>>>>> origin/main
=======
<<<<<<< main
                return JsonSerializer.Deserialize<List<ReActStep>>(text) ?? [];
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
                return JsonSerializer.Deserialize<List<ReActStep>>(text) ?? [];
=======
                return JsonSerializer.Deserialize<List<ReActStep>>(text) ?? new List<ReActStep>();
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
            }
            catch
            {
                throw new InvalidOperationException(
                    $"Failed to deserialize steps for session {sessionId}, data={text}");
            }
        }

<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        return [];
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
        return [];
=======
=======
>>>>>>> origin/main
=======
<<<<<<< main
        return [];
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        return [];
=======
        return new List<ReActStep>();
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
    }

    /// <inheritdoc/>
    public async Task SaveReActStepsAsync(string sessionId, string stepId, List<ReActStep> steps)
    {
        var json = JsonSerializer.Serialize(steps);
        await this._memoryStore.UpsertAsync(this._collectionName, this.CreateMemoryRecord(this.GetStepsStorageKey(sessionId, stepId), json))
            .ConfigureAwait(false);
    }

    private static async Task<FlowStatusProvider> InitializeProviderStoreAsync(FlowStatusProvider flowProvider, CancellationToken cancellationToken = default)
    {
        if (!await flowProvider._memoryStore.DoesCollectionExistAsync(flowProvider._collectionName, cancellationToken).ConfigureAwait(false))
        {
            await flowProvider._memoryStore.CreateCollectionAsync(flowProvider._collectionName, cancellationToken).ConfigureAwait(false);
        }

        return flowProvider;
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
