// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Azure;
using Azure.AI.OpenAI.Assistants;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Experimental.Agents.Exceptions;
using Microsoft.SemanticKernel.Experimental.Agents.Extensions;
using Microsoft.SemanticKernel.Experimental.Agents.Filters;

namespace Microsoft.SemanticKernel.Experimental.Agents.Agents;

#pragma warning disable IDE0290 // Use primary constructor

/// <summary>
/// A <see cref="KernelAgent"/> specialization based on Open AI Assistant / GPT.
/// </summary>
public sealed partial class GptAgent : KernelAgent
{
    /// <summary>
    /// A <see cref="AgentChannel"/> specialization for use with <see cref="GptAgent"/>.
    /// </summary>
    private sealed class GptChannel : AgentChannel<GptAgent>
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
        private readonly Dictionary<string, ToolDefinition[]> _agentTools;
        private readonly Dictionary<string, string> _agentNames; // $$$ WHY ???

        /// <inheritdoc/>
        protected internal override async Task RecieveAsync(IEnumerable<ChatMessageContent> history, CancellationToken cancellationToken)
        {
            foreach (var message in history)
            {
                if (string.IsNullOrWhiteSpace(message.Content))
                {
                    continue;
                }

                string? actorLabel = null;
                if (message.Role == AuthorRole.Assistant) // $$$ NEEDED ??? ALWAYS? NEVER?
                {
                    actorLabel = $"{message.Name ?? message.Role.Label}: ";
                }

                // $$$ RETRY !!!
                await this._client.CreateMessageAsync(
                    this._threadId,
                    MessageRole.User,
                    $"{actorLabel}{message.Content}",
                    fileIds: null,
                    metadata: null,
                    cancellationToken).ConfigureAwait(false);
            }
        }

        /// <inheritdoc/>
        protected internal override async IAsyncEnumerable<ChatMessageContent> InvokeAsync(
            GptAgent agent,
            ChatMessageContent? input,
            [EnumeratorCancellation] CancellationToken cancellationToken = default)
        {
            if (input.TryGetContent(out var content))
            {
                await this._client.CreateMessageAsync(this._threadId, MessageRole.User, content, fileIds: null, metadata: null, cancellationToken).ConfigureAwait(false);
            }

            if (!this._agentTools.TryGetValue(agent.Id, out var tools))
            {
                tools = [.. agent.Tools, .. agent.Kernel.Plugins.SelectMany(p => p.Select(f => f.ToToolDefinition(p.Name)))];
                this._agentTools.Add(agent.Id, tools);
            }

            if (!this._agentNames.ContainsKey(agent.Id) && !string.IsNullOrWhiteSpace(agent.Name))
            {
                this._agentNames.Add(agent.Id, agent.Name!);
            }

            string instructions = await agent.FormatInstructionsAsync(cancellationToken).ConfigureAwait(false);
            CreateRunOptions options =
                new(agent.Id)
                {
                    OverrideInstructions = instructions,
                    OverrideTools = tools,
                };

            // Create run
            ThreadRun run = await this._client.CreateRunAsync(this._threadId, options, cancellationToken).ConfigureAwait(false);

            // Poll until actionable
            await PollRunStatus().ConfigureAwait(false);

            // Evaluate status and process steps and messages, as encountered.
            HashSet<string> processedMessageIds = [];
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

                    // Refresh run as it goes back into pending state after posting function results. // $$$ PENDING MISNOMER
                    await PollRunStatus(force: true).ConfigureAwait(false);

                    steps = await this._client.GetRunStepsAsync(run, cancellationToken: cancellationToken).ConfigureAwait(false);
                }

                var messageDetails =
                    steps
                        .OrderBy(s => s.CompletedAt)
                        .Select(s => s.StepDetails)
                        .OfType<RunStepMessageCreationDetails>()
                        .Where(d => !processedMessageIds.Contains(d.MessageCreation.MessageId));

                foreach (var detail in messageDetails)
                {
                    ThreadMessage? message = null;

                    bool retry = false;
                    int count = 0;
                    do
                    {
                        try
                        {
                            PageableList<MessageFile> files = await this._client.GetMessageFilesAsync(this._threadId, detail.MessageCreation.MessageId, cancellationToken: cancellationToken).ConfigureAwait(false);
                            //var messages = await this._client.GetMessagesAsync(this._threadId, cancellationToken: cancellationToken).ConfigureAwait(false);
                            message = await this._client.GetMessageAsync(this._threadId, detail.MessageCreation.MessageId, cancellationToken).ConfigureAwait(false); // $$$ BUG: IMAGE FILES !!!
                        }
                        catch (RequestFailedException exception)
                        {
                            // Step says message exists.  Try again.
                            retry = exception.Status == (int)HttpStatusCode.NotFound && count < 3;
                        }
                        ++count;
                    }
                    while (retry);

                    if (message != null)
                    {
                        var role = new AuthorRole(message.Role.ToString());

                        foreach (var itemContent in message.ContentItems)
                        {
                            if (itemContent is MessageTextContent contentMessage)
                            {
                                var textContent = contentMessage.Text.Trim();
                                if (!string.IsNullOrWhiteSpace(textContent))
                                {
                                    yield return
                                        new ChatMessageContent(role, textContent, name: agent.Name)
                                        {
                                            Source = new AgentMessageSource(agent.Id, message.Id).ToJson()
                                        };
                                }
                            }

                            if (itemContent is MessageImageFileContent contentImage)
                            {
                                yield return new ChatMessageContent(role, contentImage.FileId, name: agent.Name) // $$$ FILEID
                                {
                                    Source = new AgentMessageSource(agent.Id, message.Id).ToJson()
                                };
                            }
                        }
                    }

                    processedMessageIds.Add(detail.MessageCreation.MessageId);
                }
            }
            while (run.Status != RunStatus.Completed);

            async Task PollRunStatus(bool force = false)
            {
                int count = 0;

                do
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
                while (s_pollingStates.Contains(run.Status));
            }

            IEnumerable<Task<ToolOutput>> ExecuteStep(RunStep step, CancellationToken cancellationToken)
            {
                // Process all of the steps that require action
                if (step.Status == RunStepStatus.InProgress && step.StepDetails is RunStepToolCallDetails callDetails)
                {
                    foreach (var toolCall in callDetails.ToolCalls.OfType<RunStepFunctionToolCall>())
                    {
                        // Run function
                        yield return ProcessFunctionStepAsync(toolCall.Id, toolCall, cancellationToken);
                    }
                }
            }

            async Task<ToolOutput> ProcessFunctionStepAsync(string callId, RunStepFunctionToolCall functionDetails, CancellationToken cancellationToken)
            {
                var result = await InvokeFunctionCallAsync().ConfigureAwait(false);
                if (result is not string toolResult)
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

                    return result.GetValue<string>() ?? string.Empty;
                }
            }
        }

        /// <inheritdoc/>
        protected internal override async IAsyncEnumerable<ChatMessageContent> GetHistoryAsync([EnumeratorCancellation] CancellationToken cancellationToken)
        {
            PageableList<ThreadMessage> messages;

            string? lastId = null;
            do
            {
                messages = await this._client.GetMessagesAsync(this._threadId, limit: 100, ListSortOrder.Descending, after: lastId, null, cancellationToken).ConfigureAwait(false);
                foreach (var message in messages)
                {
                    var role = new AuthorRole(message.Role.ToString());

                    string? assistantName = null;
                    if (!string.IsNullOrWhiteSpace(message.AssistantId) &&
                        !this._agentNames.TryGetValue(message.AssistantId, out assistantName))
                    {
                        Assistant assistant = await this._client.GetAssistantAsync(message.AssistantId, cancellationToken).ConfigureAwait(false);
                        if (!string.IsNullOrWhiteSpace(assistant.Name))
                        {
                            this._agentNames.Add(assistant.Id, assistant.Name!);
                        }
                    }

                    foreach (var content in message.ContentItems)
                    {
                        if (content is MessageTextContent contentMessage)
                        {
                            yield return new ChatMessageContent(role, contentMessage.Text.Trim(), name: assistantName ?? message.AssistantId);
                        }

                        if (content is MessageImageFileContent contentImage)
                        {
                            yield return new ChatMessageContent(role, contentImage.FileId, name: assistantName ?? message.AssistantId);
                        }
                    }

                    lastId = message.Id;
                }
            }
            while (messages.HasMore);
        }

        /// <summary>
        /// Initializes a new instance of the <see cref="GptChannel"/> class.
        /// </summary>
        public GptChannel(AssistantsClient client, string threadId)
        {
            this._client = client;
            this._threadId = threadId;
            this._agentTools = [];
            this._agentNames = [];
        }
    }
}
