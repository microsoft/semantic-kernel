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
using Microsoft.SemanticKernel.Agents.Extensions;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// A <see cref="KernelAgent"/> specialization based on Open AI Assistant / GPT.
/// </summary>
public sealed partial class OpenAIAssistantAgent : KernelAgent
{
    private const char Functiondelimiter = '-';

    /// <summary>
    /// A <see cref="AgentChannel"/> specialization for use with <see cref="OpenAIAssistantAgent"/>.
    /// </summary>
    private sealed class Channel : AgentChannel<OpenAIAssistantAgent>
    {
        private static readonly TimeSpan s_pollingInterval = TimeSpan.FromMilliseconds(500);
        private static readonly TimeSpan s_pollingBackoff = TimeSpan.FromSeconds(1);

        private static readonly HashSet<RunStatus> s_pollingStates =
            new()
            {
                RunStatus.Queued,
                RunStatus.InProgress,
                RunStatus.Cancelling,
            };

        private static readonly HashSet<RunStatus> s_terminalStates =
            new()
            {
                RunStatus.Expired,
                RunStatus.Failed,
                RunStatus.Cancelled,
            };

        private readonly AssistantsClient _client;
        private readonly string _threadId;
        private readonly Dictionary<string, ToolDefinition[]> _agentTools;
        private readonly Dictionary<string, string> _agentNames; // Cache agent names by their identifier for GetHistoryAsync()

        /// <inheritdoc/>
        protected override async Task ReceiveAsync(IEnumerable<ChatMessageContent> history, CancellationToken cancellationToken)
        {
            foreach (var message in history)
            {
                if (string.IsNullOrWhiteSpace(message.Content))
                {
                    continue;
                }

                await this._client.CreateMessageAsync(
                    this._threadId,
                    MessageRole.User,
                    message.Content,
                    fileIds: null,
                    metadata: null,
                    cancellationToken).ConfigureAwait(false);
            }
        }

        /// <inheritdoc/>
        protected override async IAsyncEnumerable<ChatMessageContent> InvokeAsync(
            OpenAIAssistantAgent agent,
            [EnumeratorCancellation] CancellationToken cancellationToken)
        {
            if (agent.IsDeleted)
            {
                throw new KernelException($"Agent Failure - {nameof(OpenAIAssistantAgent)} agent is deleted: {agent.Id}.");
            }

            if (!this._agentTools.TryGetValue(agent.Id, out var tools))
            {
                tools = agent.Tools.Concat(agent.Kernel.Plugins.SelectMany(p => p.Select(f => f.ToToolDefinition(p.Name, Functiondelimiter)))).ToArray();
                this._agentTools.Add(agent.Id, tools);
            }

            if (!this._agentNames.ContainsKey(agent.Id) && !string.IsNullOrWhiteSpace(agent.Name))
            {
                this._agentNames.Add(agent.Id, agent.Name!);
            }

            CreateRunOptions options =
                new(agent.Id)
                {
                    OverrideInstructions = agent.Instructions,
                    OverrideTools = tools,
                };

            // Create run
            ThreadRun run = await agent._client.CreateRunAsync(this._threadId, options, cancellationToken).ConfigureAwait(false);

            // Evaluate status and process steps and messages, as encountered.
            var processedMessageIds = new HashSet<string>();

            do
            {
                // Poll run and steps until actionable
                var steps = await PollRunStatusAsync().ConfigureAwait(false);

                // Is in terminal state?
                if (s_terminalStates.Contains(run.Status))
                {
                    throw new KernelException($"Agent Failure - Run terminated: {run.Status} [{run.Id}]: {run.LastError?.Message ?? "Unknown"}");
                }

                // Is tool action required?
                if (run.Status == RunStatus.RequiresAction)
                {
                    // Execute functions in parallel and post results at once.
                    var tasks = steps.Data.SelectMany(step => ExecuteStep(step, cancellationToken)).ToArray();
                    if (tasks.Length > 0)
                    {
                        var results = await Task.WhenAll(tasks).ConfigureAwait(false);

                        await this._client.SubmitToolOutputsToRunAsync(run, results, cancellationToken).ConfigureAwait(false);
                    }
                }

                // Enumerate completed messages
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
                            message = await this._client.GetMessageAsync(this._threadId, detail.MessageCreation.MessageId, cancellationToken).ConfigureAwait(false);
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
                        AuthorRole role = new(message.Role.ToString());

                        foreach (MessageContent itemContent in message.ContentItems)
                        {
                            if (itemContent is MessageTextContent contentMessage)
                            {
                                var textContent = contentMessage.Text.Trim();

                                if (!string.IsNullOrWhiteSpace(textContent))
                                {
                                    ChatMessageContent messageContent =
                                        new(role, textContent)
                                        {
                                            AuthorName = agent.Name
                                        };

                                    foreach (MessageTextAnnotation annotation in contentMessage.Annotations)
                                    {
                                        messageContent.Items.Add(new AnnotationContent(annotation));
                                    }

                                    yield return messageContent;
                                }
                            }

                            if (itemContent is MessageImageFileContent contentImage)
                            {
                                yield return
                                    new ChatMessageContent(role, new ChatMessageContentItemCollection() { new FileReferenceContent(contentImage.FileId) })
                                    {
                                        AuthorName = agent.Name,
                                    };
                            }
                        }
                    }

                    processedMessageIds.Add(detail.MessageCreation.MessageId);
                }
            }
            while (RunStatus.Completed != run.Status);

            async Task<PageableList<RunStep>> PollRunStatusAsync()
            {
                int count = 0;

                do
                {
                    // Reduce polling frequency after a couple attempts
                    await Task.Delay(count >= 2 ? s_pollingInterval : s_pollingBackoff, cancellationToken).ConfigureAwait(false);
                    ++count;

                    try
                    {
                        run = await agent._client.GetRunAsync(this._threadId, run.Id, cancellationToken).ConfigureAwait(false);
                    }
                    catch (Exception exception) when (!exception.IsCriticalException())
                    {
                        // Retry anyway..
                    }
                }
                while (s_pollingStates.Contains(run.Status));

                //return await this._restContext.GetRunStepsAsync(this.ThreadId, this.Id, cancellationToken).ConfigureAwait(false);
                return await this._client.GetRunStepsAsync(run, cancellationToken: cancellationToken).ConfigureAwait(false);
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
                    var function = agent.Kernel.GetAssistantTool(functionDetails.Name, Functiondelimiter);

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
        protected override async IAsyncEnumerable<ChatMessageContent> GetHistoryAsync([EnumeratorCancellation] CancellationToken cancellationToken)
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
                            yield return new ChatMessageContent(role, contentMessage.Text.Trim()) { AuthorName = assistantName ?? message.AssistantId };
                        }

                        if (content is MessageImageFileContent contentImage)
                        {
                            yield return
                                new ChatMessageContent(role, new ChatMessageContentItemCollection() { new FileReferenceContent(contentImage.FileId) })
                                {
                                    AuthorName = assistantName ?? message.AssistantId,
                                };
                        }
                    }

                    lastId = message.Id;
                }
            }
            while (messages.HasMore);
        }

        /// <summary>
        /// Initializes a new instance of the <see cref="Channel"/> class.
        /// </summary>
        public Channel(AssistantsClient client, string threadId)
        {
            this._client = client;
            this._threadId = threadId;
            this._agentTools = new();
            this._agentNames = new();
        }
    }
}
