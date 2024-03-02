// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI.Assistants;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Experimental.Agents.Exceptions;
using Microsoft.SemanticKernel.Experimental.Agents.Extensions;

namespace Microsoft.SemanticKernel.Experimental.Agents.Gpt;

/// <summary>
/// A <see cref="AgentChannel"/> specialization for use with <see cref="GptAgent"/>.
/// </summary>
public sealed class GptChannel : AgentChannel
{
    private static readonly TimeSpan s_pollingInterval = TimeSpan.FromMilliseconds(500);
    private static readonly TimeSpan s_pollingBackoff = TimeSpan.FromSeconds(1);
    private static readonly HashSet<RunStatus>
        s_pollingStates =
        [
            RunStatus.Queued,
            RunStatus.InProgress
        ];

    private readonly AssistantsClient _client;
    private readonly string _threadId;
    private readonly Dictionary<string, ToolDefinition[]> _tools;

    /// <inheritdoc/>
    public override async Task RecieveAsync(IEnumerable<ChatMessageContent> history, CancellationToken cancellationToken)
    {
        foreach (var message in history)
        {
            if (string.IsNullOrWhiteSpace(message.Content))
            {
                continue;
            }

            string actorName;
            if (message.Role == AuthorRole.Assistant)
            {
                actorName = message.Name ?? message.Role.Label;
            }
            else
            {
                actorName = message.Role.Label;
            }

            await this._client.CreateMessageAsync(
                this._threadId,
                MessageRole.User,
                $"{actorName}: {message.Content}",
                fileIds: null,
                metadata: null,
                cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc/>
    public override async IAsyncEnumerable<ChatMessageContent> InvokeAsync(KernelAgent agent, ChatMessageContent? input, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (input != null)
        {
            var userMessage = await this._client.CreateMessageAsync(this._threadId, MessageRole.User, input.Content, fileIds: null, metadata: null, cancellationToken).ConfigureAwait(false);
            yield return input; // $$$ TRANSFORM USERMESSAGE
        }

        if (!this._tools.TryGetValue(agent.Id, out var tools))
        {
            tools = agent.Kernel.Plugins.SelectMany(p => p.Select(f => f.ToToolDefinition(p.Name))).ToArray(); // $$$ CODE / RETRIEVAL
            this._tools.Add(agent.Id, tools);
        }

        var options =
            new CreateRunOptions(agent.Id)
            {
                OverrideInstructions = null, // $$$ TEMPLATING ???
                OverrideTools = tools,
            };

        // Create run
        ThreadRun run = await this._client.CreateRunAsync(this._threadId, options, cancellationToken).ConfigureAwait(false);

        // Poll until actionable
        await PollRunStatus().ConfigureAwait(false);

        // Evaluate status and process steps and messages, as encountered.
        var processedMessageIds = new HashSet<string>();
        do
        {
            if (run.Status == RunStatus.Failed)
            {
                throw new AgentException($"Unexpected failure processing run: {run.Id}: {run.LastError.Message ?? "Unknown"}");
            }

            PageableList<RunStep> steps = await this._client.GetRunStepsAsync(run, cancellationToken: cancellationToken).ConfigureAwait(false);

            if (run.Status == RunStatus.RequiresAction)
            {
                // Execute functions in parallel and post results at once.
                var tasks = steps.Data.SelectMany(step => ExecuteStep(step, cancellationToken)).ToArray();
                await Task.WhenAll(tasks).ConfigureAwait(false);

                var results = tasks.Select(t => t.Result).ToArray();

                await this._client.SubmitToolOutputsToRunAsync(run, results, cancellationToken).ConfigureAwait(false);

                // Refresh run as it goes back into pending state after posting function results.
                await PollRunStatus(force: true).ConfigureAwait(false);
            }

            var messageDetails =
                steps
                    .OrderBy(s => s.CompletedAt)
                    .Select(s => s.StepDetails)
                    .OfType<RunStepMessageCreationDetails>()
                    .Where(d => !processedMessageIds.Contains(d.MessageCreation.MessageId));

            foreach (var detail in messageDetails)
            {
                ThreadMessage message = await this._client.GetMessageAsync(this._threadId, detail.MessageCreation.MessageId, cancellationToken).ConfigureAwait(false); // $$$ RETRY 404
                var role = new AuthorRole(message.Role.ToString());

                foreach (var content in message.ContentItems)
                {
                    if (content is MessageTextContent contentMessage)
                    {
                        yield return new ChatMessageContent(role, contentMessage.Text.Trim(), agent.Name);
                        continue;
                    }

                    if (content is MessageImageFileContent contentImage)
                    {
                        yield return new ChatMessageContent(role, contentImage.FileId, agent.Name); // $$$ FILE HANDLING
                        continue;
                    }
                }

                processedMessageIds.Add(message.Id);
            }
        }
        while (run.Status != RunStatus.Completed);

        async Task PollRunStatus(bool force = false)
        {
            int count = 0;

            // Ignore model status when forced.
            while (force || s_pollingStates.Contains(run.Status))
            {
                if (!force)
                {
                    // Reduce polling frequency after a couple attempts
                    await Task.Delay(count >= 2 ? s_pollingInterval : s_pollingBackoff, cancellationToken).ConfigureAwait(false);
                    ++count;
                }

                force = false;

                try
                {
                    run = await this._client.GetRunAsync(this._threadId, run.Id, cancellationToken).ConfigureAwait(false);
                }
                catch (Exception exception) when (!exception.IsCriticalException())
                {
                    // Retry anyway..
                }
            }
        }

        IEnumerable<Task<ToolOutput>> ExecuteStep(RunStep step, CancellationToken cancellationToken)
        {
            // Process all of the steps that require action
            if (step.Status == RunStepStatus.InProgress && step.StepDetails is RunStepToolCallDetails callDetails)
            {
                foreach (var toolCall in callDetails.ToolCalls.OfType<RunStepFunctionToolCall>()) // $$$ CODE / RETRIEVAL ???
                {
                    // Run function
                    yield return ProcessFunctionStepAsync(toolCall.Id, toolCall, cancellationToken);
                }
            }
        }

        async Task<ToolOutput> ProcessFunctionStepAsync(string callId, RunStepFunctionToolCall functionDetails, CancellationToken cancellationToken)
        {
            var result = await InvokeFunctionCallAsync().ConfigureAwait(false);
            var toolResult = result as string;
            if (toolResult == null)
            {
                toolResult = JsonSerializer.Serialize(result);
            }

            return new ToolOutput(callId, toolResult!);

            async Task<object> InvokeFunctionCallAsync()
            {
                var function = agent.Kernel.GetAssistantTool(functionDetails.Name);

                var functionArguments = new KernelArguments();
                if (!string.IsNullOrWhiteSpace(functionDetails.Arguments))
                {
                    var arguments = JsonSerializer.Deserialize<Dictionary<string, object>>(functionDetails.Arguments)!;
                    foreach (var argument in arguments)
                    {
                        functionArguments[argument.Key] = argument.Value.ToString();
                    }
                }

                var result = await function.InvokeAsync(agent.Kernel, functionArguments, cancellationToken).ConfigureAwait(false);
                if (result.ValueType == typeof(AgentResponse)) // $$$ WTF ???
                {
                    return result.GetValue<AgentResponse>()!;
                }

                return result.GetValue<string>() ?? string.Empty;
            }
        }
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="GptChannel"/> class.
    /// </summary>
    internal GptChannel(AssistantsClient client, string threadId)
    {
        this._client = client;
        this._threadId = threadId;
        this._tools = [];
    }
}
