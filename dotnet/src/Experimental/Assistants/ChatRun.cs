// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Assistants.Extensions;
using Microsoft.SemanticKernel.Experimental.Assistants.Models;

namespace Microsoft.SemanticKernel.Experimental.Assistants;

/// <summary>
/// $$$
/// </summary>
public sealed class ChatRun : IChatRun
{
    /// <inheritdoc/>
    public string Id => this._model.Id;

    /// <inheritdoc/>
    public string AssistantId => this._model.AssistantId;

    /// <inheritdoc/>
    public string ThreadId => this._model.ThreadId;

    private const string ActionState = "requires_action";
    private const string FailedState = "failed";

    private static readonly HashSet<string> s_pollingStates =
        new(StringComparer.OrdinalIgnoreCase)
        {
            "queued",
            "in_progress",
        };

    private readonly IOpenAIRestContext _restContext;
    private ThreadRunModel _model;

    /// <summary>
    /// $$$
    /// </summary>
    public static async Task<ChatRun> CreateAsync(
        IOpenAIRestContext restContext,
        string threadId,
        string assistantId,
        CancellationToken cancellationToken = default)
    {
        var resultModel =
            await restContext.CreateRunAsync(threadId, assistantId, cancellationToken).ConfigureAwait(false) ??
            throw new InvalidOperationException("$$$");

        return new ChatRun(resultModel, restContext);
    }

    /// <summary>
    /// $$$
    /// </summary>
    public static async Task<ChatRun> GetRunAsync(
        IOpenAIRestContext restContext,
        string threadId,
        string runId,
        CancellationToken cancellationToken = default)
    {
        var resultModel =
            await restContext.GetRunAsync(threadId, runId, cancellationToken).ConfigureAwait(false) ??
            throw new InvalidOperationException("$$$");

        return new ChatRun(resultModel, restContext);
    }

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public async Task<string> GetResultAsync(CancellationToken cancellationToken = default)
    {
        while (s_pollingStates.Contains(this._model.Status))
        {
            try
            {
                this._model = await this._restContext.GetRunAsync(this.Id, this.AssistantId, cancellationToken).ConfigureAwait(false);
            }
            catch
            {
                // $$$
            }
        }

        if (ActionState.Equals(this._model.Status, StringComparison.OrdinalIgnoreCase))
        {
            // $$$
        }

        if (FailedState.Equals(this._model.Status, StringComparison.OrdinalIgnoreCase))
        {
            return this._model.LastError?.Message ?? "Unexpected failure";
        }

        var steps = await this._restContext.GetRunStepsAsync(this.ThreadId, this.Id, cancellationToken).ConfigureAwait(false);

        return steps.Last().Object;
    }

    private ChatRun(ThreadRunModel model, IOpenAIRestContext restContext)
    {
        this._model = model;
        this._restContext = restContext;
    }
}
