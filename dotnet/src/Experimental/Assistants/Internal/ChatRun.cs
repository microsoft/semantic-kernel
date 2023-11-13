// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
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

        // Is tool action required?
        if (ActionState.Equals(this._model.Status, StringComparison.OrdinalIgnoreCase))
        {
            // TODO: @chris make this more efficient through parallelization
            //foreach (ThreadRunStepModel threadRunStep in threadRunSteps.Data)
            //{
            //    // Retrieve all of the steps that require action
            //    if (threadRunStep.Status == "in_progress" && threadRunStep.StepDetails.Type == "tool_calls")
            //    {
            //        foreach (var toolCall in threadRunStep.StepDetails.ToolCalls)
            //        {
            //            // Run function
            //            //var result = await this.InvokeFunctionCallAsync(kernel, toolCall.Function.Name, toolCall.Function.Arguments).ConfigureAwait(false);

            //            //// Update the thread run
            //            //threadRunModel = await this.SubmitToolOutputsToRunAsync(threadRunModel.Id, toolCall.Id, result).ConfigureAwait(false);
            //        }
            //    }
            //}
        }

        // Did fail?
        if (FailedState.Equals(this._model.Status, StringComparison.OrdinalIgnoreCase))
        {
            throw new SKException($"Unexpected failure processing run: {this.Id}: {this._model.LastError?.Message ?? "Unknown"}");
        }

        var steps = await this._restContext.GetRunStepsAsync(this.ThreadId, this.Id, cancellationToken).ConfigureAwait(false);
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

    //private async Task<string> InvokeFunctionCallAsync(IKernel kernel, string name, string arguments)
    //{
    //    // split name
    //    string[] nameParts = name.Split('-');

    //    // get function from kernel
    //    var function = kernel.Functions.GetFunction(nameParts[0], nameParts[1]);
    //    // TODO: @chris: change back to Dictionary<string, object>
    //    Dictionary<string, object> variables = JsonSerializer.Deserialize<Dictionary<string, object>>(arguments)!;

    //    var results = await kernel.RunAsync(function /*, variables*/).ConfigureAwait(false);

    //    return results.GetValue<string>()!;
    //}

    //private async Task<ThreadRunModel> SubmitToolOutputsToRunAsync(string runId, string toolCallId, string output)
    //{
    //    var requestData = new
    //    {
    //        tool_outputs = new[] {
    //            new {
    //                tool_call_id = toolCallId,
    //                output = output
    //            }
    //        }
    //    };

    //    string url = "https://api.openai.com/v1/threads/" + this.Id + "/runs/" + runId + "/submit_tool_outputs";
    //    using var httpRequestMessage = HttpRequest.CreatePostRequest(url, requestData);
    //    httpRequestMessage.Headers.Add("Authorization", $"Bearer {this._apiKey}");
    //    httpRequestMessage.Headers.Add("OpenAI-Beta", "assistants=v1");

    //    var response = await this._client.SendAsync(httpRequestMessage).ConfigureAwait(false);

    //    string responseBody = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
    //    return JsonSerializer.Deserialize<ThreadRunModel>(responseBody)!;
    //}
}
