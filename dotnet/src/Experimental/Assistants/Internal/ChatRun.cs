// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Experimental.Assistants.Extensions;
using Microsoft.SemanticKernel.Experimental.Assistants.Models;

namespace Microsoft.SemanticKernel.Experimental.Assistants.Internal;

/// <summary>
/// Represents an execution run on a thread.
/// </summary>
internal sealed class ChatRun : IChatRun
{
    /// <inheritdoc/>
    public string Id => this._model.Id;

    /// <inheritdoc/>
    public string AssistantId => this._model.AssistantId;

    /// <inheritdoc/>
    public string ThreadId => this._model.ThreadId;

    private const string ActionState = "requires_action";
    private const string FailedState = "failed";
    private static readonly TimeSpan s_pollingInterval = TimeSpan.FromMilliseconds(200);

    private static readonly HashSet<string> s_pollingStates =
        new(StringComparer.OrdinalIgnoreCase)
        {
            "queued",
            "in_progress",
        };

    private readonly IOpenAIRestContext _restContext;
    private ThreadRunModel _model;

    /// <inheritdoc/>
    public async Task<IList<string>> GetResultAsync(CancellationToken cancellationToken = default)
    {
        // Poll until actionable
        while (s_pollingStates.Contains(this._model.Status))
        {
            await Task.Delay(s_pollingInterval, cancellationToken).ConfigureAwait(false);

            try
            {
                this._model = await this._restContext.GetRunAsync(this.ThreadId, this.Id, cancellationToken).ConfigureAwait(false);
            }
            catch (Exception exception) when (!exception.IsCriticalException())
            {
                // Retry anyway..
            }
        }

        // Retrieve steps
        var steps = await this._restContext.GetRunStepsAsync(this.ThreadId, this.Id, cancellationToken).ConfigureAwait(false);

        // Is tool action required?
        if (ActionState.Equals(this._model.Status, StringComparison.OrdinalIgnoreCase))
        {
            var tasks = steps.Data.SelectMany(step => this.ExecuteStep(step, cancellationToken)).ToArray();

            await Task.WhenAll(tasks).ConfigureAwait(false);

            // Refresh steps $$$ ???
            steps = await this._restContext.GetRunStepsAsync(this.ThreadId, this.Id, cancellationToken).ConfigureAwait(false);
        }

        // Did fail?
        if (FailedState.Equals(this._model.Status, StringComparison.OrdinalIgnoreCase))
        {
            throw new SKException($"Unexpected failure processing run: {this.Id}: {this._model.LastError?.Message ?? "Unknown"}");
        }

        var messageIds =
            steps.Data
                .Where(s => s.StepDetails.MessageCreation != null)
                .Select(s => s.StepDetails.MessageCreation!.MessageId)
                .ToArray();

        return messageIds; // TODO: @chris HAXX
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatRun"/> class.
    /// </summary>
    internal ChatRun(ThreadRunModel model, IOpenAIRestContext restContext)
    {
        this._model = model;
        this._restContext = restContext;
    }

    private IEnumerable<Task> ExecuteStep(ThreadRunStepModel step, CancellationToken cancellationToken)
    {
        // Process all of the steps that require action
        if (step.Status == "in_progress" && step.StepDetails.Type == "tool_calls")
        {
            foreach (var toolCall in step.StepDetails.ToolCalls)
            {
                // Run function
                yield return this.ProcessFunctionStepAsync(toolCall.Id, toolCall.Function, cancellationToken); // $$$ NULLABILITY
            }
        }
    }

    private async Task ProcessFunctionStepAsync(string callId, ThreadRunStepModel.FunctionDetailsModel functionDetails, CancellationToken cancellationToken)
    {
        var result = await InvokeFunctionCallAsync().ConfigureAwait(false);

        await this._restContext.AddToolOutputAsync(this.ThreadId, this.Id, callId, result, cancellationToken).ConfigureAwait(false);

        async Task<string> InvokeFunctionCallAsync()
        {
            // split name $$$
            //string[] nameParts = name.Split('-');
            // get function from kernel
            //var function = (ISKFunction)null!;
            //var kernel = (IKernel)null!;

            //// TODO: @chris: change back to Dictionary<string, object> $$$
            ////Dictionary<string, object> variables = JsonSerializer.Deserialize<Dictionary<string, object>>(arguments)!;
            //var variables = new ContextVariables(); // $$$
            //var results = await kernel.RunAsync(function, variables, cancellationToken).ConfigureAwait(false); // $$$ TRY/CATCH

            await Task.Delay(0, cancellationToken).ConfigureAwait(false);

            //return results.GetValue<string>()!;
            return DateTime.UtcNow.ToString(CultureInfo.InvariantCulture);
        }
    }
}
