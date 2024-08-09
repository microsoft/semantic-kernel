// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Agents.Exceptions;
using Microsoft.SemanticKernel.Experimental.Agents.Extensions;
using Microsoft.SemanticKernel.Experimental.Agents.Models;

namespace Microsoft.SemanticKernel.Experimental.Agents.Internal;

/// <summary>
/// Represents an execution run on a thread.
/// </summary>
internal sealed class ChatRun
{
    /// <summary>
    /// ID of this run.
    /// </summary>
    public string Id => this._model.Id;

    /// <summary>
    /// ID of the assistant used for execution of this run.
    /// </summary>
    public string AgentId => this._model.AssistantId;

    /// <summary>
    /// ID of the thread that was executed on as a part of this run.
    /// </summary>
    public string ThreadId => this._model.ThreadId;

    /// <summary>
    /// Optional arguments for injection into function-calling.
    /// </summary>
    public KernelArguments? Arguments { get; init; }

    private const string ActionState = "requires_action";
    private const string CompletedState = "completed";
    private static readonly TimeSpan s_pollingInterval = TimeSpan.FromMilliseconds(500);
    private static readonly TimeSpan s_pollingBackoff = TimeSpan.FromSeconds(1);

    private static readonly HashSet<string> s_pollingStates =
        new(StringComparer.OrdinalIgnoreCase)
        {
            "queued",
            "in_progress",
            "cancelling",
        };

    private static readonly HashSet<string> s_terminalStates =
        new(StringComparer.OrdinalIgnoreCase)
        {
            "expired",
            "failed",
            "cancelled",
        };

    private readonly OpenAIRestContext _restContext;
    private readonly Kernel _kernel;

    private ThreadRunModel _model;

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> GetResultAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var processedMessageIds = new HashSet<string>();

        do
        {
            // Poll run and steps until actionable
            var steps = await PollRunStatusAsync().ConfigureAwait(false);

            // Is in terminal state?
            if (s_terminalStates.Contains(this._model.Status))
            {
                throw new AgentException($"Run terminated - {this._model.Status} [{this.Id}]: {this._model.LastError?.Message ?? "Unknown"}");
            }

            // Is tool action required?
            if (ActionState.Equals(this._model.Status, StringComparison.OrdinalIgnoreCase))
            {
                // Execute functions in parallel and post results at once.
                var tasks = steps.Data.SelectMany(step => this.ExecuteStep(step, cancellationToken)).ToArray();
                if (tasks.Length > 0)
                {
                    var results = await Task.WhenAll(tasks).ConfigureAwait(false);
                    await this._restContext.AddToolOutputsAsync(this.ThreadId, this.Id, results, cancellationToken).ConfigureAwait(false);
                }
            }

            // Enumerate completed messages
            var newMessageIds =
                steps.Data
                    .Where(s => s.StepDetails.MessageCreation is not null)
                    .Select(s => (s.StepDetails.MessageCreation!.MessageId, s.CompletedAt))
                    .Where(t => !processedMessageIds.Contains(t.MessageId))
                    .OrderBy(t => t.CompletedAt)
                    .Select(t => t.MessageId);

            foreach (var messageId in newMessageIds)
            {
                processedMessageIds.Add(messageId);
                yield return messageId;
            }
        }
        while (!CompletedState.Equals(this._model.Status, StringComparison.OrdinalIgnoreCase));

        async Task<ThreadRunStepListModel> PollRunStatusAsync()
        {
            int count = 0;

            do
            {
                // Reduce polling frequency after a couple attempts
                await Task.Delay(count >= 2 ? s_pollingInterval : s_pollingBackoff, cancellationToken).ConfigureAwait(false);
                ++count;

                try
                {
                    this._model = await this._restContext.GetRunAsync(this.ThreadId, this.Id, cancellationToken).ConfigureAwait(false);
                }
                catch (Exception exception) when (!exception.IsCriticalException())
                {
                    // Retry anyway..
                }
            }
            while (s_pollingStates.Contains(this._model.Status));

            return await this._restContext.GetRunStepsAsync(this.ThreadId, this.Id, cancellationToken).ConfigureAwait(false);
        }
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatRun"/> class.
    /// </summary>
    internal ChatRun(
        ThreadRunModel model,
        Kernel kernel,
        OpenAIRestContext restContext)
    {
        this._model = model;
        this._kernel = kernel;
        this._restContext = restContext;
    }

    private IEnumerable<Task<ToolResultModel>> ExecuteStep(ThreadRunStepModel step, CancellationToken cancellationToken)
    {
        // Process all of the steps that require action
        if (step.Status == "in_progress" && step.StepDetails.Type == "tool_calls")
        {
            foreach (var toolCall in step.StepDetails.ToolCalls)
            {
                // Run function
                yield return this.ProcessFunctionStepAsync(toolCall.Id, toolCall.Function, cancellationToken);
            }
        }
    }

    private async Task<ToolResultModel> ProcessFunctionStepAsync(string callId, ThreadRunStepModel.FunctionDetailsModel functionDetails, CancellationToken cancellationToken)
    {
        var result = await InvokeFunctionCallAsync().ConfigureAwait(false);

        return
            new ToolResultModel
            {
                CallId = callId,
                Output = ParseFunctionResult(result),
            };

        async Task<object> InvokeFunctionCallAsync()
        {
            var function = this._kernel.GetAssistantTool(functionDetails.Name);

            var functionArguments = new KernelArguments(this.Arguments ?? []);
            if (!string.IsNullOrWhiteSpace(functionDetails.Arguments))
            {
                var arguments = JsonSerializer.Deserialize<Dictionary<string, object>>(functionDetails.Arguments)!;
                foreach (var argument in arguments)
                {
                    functionArguments[argument.Key] = argument.Value.ToString();
                }
            }

            var result = await function.InvokeAsync(this._kernel, functionArguments, cancellationToken).ConfigureAwait(false);

            return result.GetValue<object>() ?? string.Empty;
        }
    }

    private static string ParseFunctionResult(object result)
    {
        if (result is string stringResult)
        {
            return stringResult;
        }

        if (result is ChatMessageContent messageResult)
        {
            return messageResult.Content ?? JsonSerializer.Serialize(messageResult);
        }

        return JsonSerializer.Serialize(result);
    }
}
