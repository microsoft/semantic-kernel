// Copyright (c) Microsoft. All rights reserved.
using System.ClientModel;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Azure;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI;
using OpenAI.Assistants;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// A <see cref="AgentChannel"/> specialization for use with <see cref="OpenAIAssistantAgent"/>.
/// </summary>
internal sealed class OpenAIAssistantChannel(AssistantClient client, string threadId, OpenAIAssistantConfiguration.PollingConfiguration pollingConfiguration)
    : AgentChannel<OpenAIAssistantAgent>
{
    private const string FunctionDelimiter = "-";

    private static readonly HashSet<RunStatus> s_pollingStatuses =
        [
            RunStatus.Queued,
            RunStatus.InProgress,
            RunStatus.Cancelling,
        ];

    private static readonly HashSet<RunStatus> s_terminalStatuses =
        [
            RunStatus.Expired,
            RunStatus.Failed,
            RunStatus.Cancelled,
        ];

    private readonly AssistantClient _client = client;
    private readonly string _threadId = threadId;
    private readonly Dictionary<string, ToolDefinition[]> _agentTools = [];
    private readonly Dictionary<string, string?> _agentNames = []; // Cache agent names by their identifier for GetHistoryAsync()

    /// <inheritdoc/>
    protected override async Task ReceiveAsync(IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken)
    {
        foreach (ChatMessageContent message in history)
        {
            if (string.IsNullOrWhiteSpace(message.Content))
            {
                continue;
            }

            MessageCreationOptions options =
                new()
                {
                    //Role = message.Role.ToMessageRole(), // %%% BUG: ASSIGNABLE
                };

            await this._client.CreateMessageAsync(
                this._threadId,
                [message.Content], // %%%
                options,
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

        if (!this._agentTools.TryGetValue(agent.Id, out ToolDefinition[]? tools))
        {
            tools = [.. agent.Tools, .. agent.Kernel.Plugins.SelectMany(p => p.Select(f => f.ToToolDefinition(p.Name, FunctionDelimiter)))];
            this._agentTools.Add(agent.Id, tools);
        }

        if (!this._agentNames.ContainsKey(agent.Id) && !string.IsNullOrWhiteSpace(agent.Name))
        {
            this._agentNames.Add(agent.Id, agent.Name);
        }

        this.Logger.LogDebug("[{MethodName}] Creating run for agent/thrad: {AgentId}/{ThreadId}", nameof(InvokeAsync), agent.Id, this._threadId);

        RunCreationOptions options =
            new()
            {
                //InstructionsOverride = agent.Instructions,
                //ParallelToolCallsEnabled = true, // %%%
                //ResponseFormat = %%%
                //ToolsOverride = tools, %%%
            };

        // Create run
        ThreadRun run = await this._client.CreateRunAsync(this._threadId, agent.Id, options, cancellationToken).ConfigureAwait(false);

        this.Logger.LogInformation("[{MethodName}] Created run: {RunId}", nameof(InvokeAsync), run.Id);

        // Evaluate status and process steps and messages, as encountered.
        HashSet<string> processedStepIds = [];
        Dictionary<string, FunctionCallContent> functionSteps = [];

        do
        {
            // Poll run and steps until actionable
            await PollRunStatusAsync().ConfigureAwait(false);

            // Is in terminal state?
            if (s_terminalStatuses.Contains(run.Status))
            {
                throw new KernelException($"Agent Failure - Run terminated: {run.Status} [{run.Id}]: {run.LastError?.Message ?? "Unknown"}");
            }

            RunStep[] steps = await this._client.GetRunStepsAsync(run).ToArrayAsync(cancellationToken).ConfigureAwait(false);

            // Is tool action required?
            if (run.Status == RunStatus.RequiresAction)
            {
                this.Logger.LogDebug("[{MethodName}] Processing run steps: {RunId}", nameof(InvokeAsync), run.Id);

                // Execute functions in parallel and post results at once.
                FunctionCallContent[] activeFunctionSteps = steps.SelectMany(step => ParseFunctionStep(agent, step)).ToArray();
                if (activeFunctionSteps.Length > 0)
                {
                    // Emit function-call content
                    yield return GenerateFunctionCallContent(agent.GetName(), activeFunctionSteps);

                    // Invoke functions for each tool-step
                    IEnumerable<Task<FunctionResultContent>> functionResultTasks = ExecuteFunctionSteps(agent, activeFunctionSteps, cancellationToken);

                    // Block for function results
                    FunctionResultContent[] functionResults = await Task.WhenAll(functionResultTasks).ConfigureAwait(false);

                    // Process tool output
                    ToolOutput[] toolOutputs = GenerateToolOutputs(functionResults);

                    await this._client.SubmitToolOutputsToRunAsync(run, toolOutputs).ConfigureAwait(false); // %%% CANCEL TOKEN
                }

                if (this.Logger.IsEnabled(LogLevel.Information)) // Avoid boxing if not enabled
                {
                    this.Logger.LogInformation("[{MethodName}] Processed #{MessageCount} run steps: {RunId}", nameof(InvokeAsync), activeFunctionSteps.Length, run.Id);
                }
            }

            // Enumerate completed messages
            this.Logger.LogDebug("[{MethodName}] Processing run messages: {RunId}", nameof(InvokeAsync), run.Id);

            IEnumerable<RunStep> completedStepsToProcess =
                steps
                    .Where(s => s.CompletedAt.HasValue && !processedStepIds.Contains(s.Id))
                    .OrderBy(s => s.CreatedAt);

            int messageCount = 0;
            foreach (RunStep completedStep in completedStepsToProcess)
            {
                if (completedStep.Type == RunStepType.ToolCalls)
                {
                    foreach (RunStepToolCall toolCall in completedStep.Details.ToolCalls)
                    {
                        ChatMessageContent? content = null;

                        // Process code-interpreter content
                        if (toolCall.ToolKind == RunStepToolCallKind.CodeInterpreter)
                        {
                            content = GenerateCodeInterpreterContent(agent.GetName(), toolCall.CodeInterpreterInput);
                        }
                        // Process function result content
                        else if (toolCall.ToolKind == RunStepToolCallKind.Function)
                        {
                            FunctionCallContent functionStep = functionSteps[toolCall.ToolCallId]; // Function step always captured on invocation
                            content = GenerateFunctionResultContent(agent.GetName(), functionStep, toolCall.FunctionOutput);
                        }

                        if (content is not null)
                        {
                            ++messageCount;

                            yield return content;
                        }
                    }
                }
                else if (completedStep.Type == RunStepType.MessageCreation)
                {
                    // Retrieve the message
                    ThreadMessage? message = await this.RetrieveMessageAsync(completedStep.Details.CreatedMessageId, cancellationToken).ConfigureAwait(false);

                    if (message is not null)
                    {
                        AuthorRole role = new(message.Role.ToString());

                        foreach (MessageContent itemContent in message.Content)
                        {
                            ChatMessageContent? content = null;

                            // Process text content
                            if (!string.IsNullOrEmpty(itemContent.Text))
                            {
                                content = GenerateTextMessageContent(agent.GetName(), role, itemContent);
                            }
                            // Process image content
                            else if (itemContent.ImageFileId != null)
                            {
                                content = GenerateImageFileContent(agent.GetName(), role, itemContent);
                            }

                            if (content is not null)
                            {
                                ++messageCount;

                                yield return content;
                            }
                        }
                    }
                }

                processedStepIds.Add(completedStep.Id);
            }

            if (this.Logger.IsEnabled(LogLevel.Information)) // Avoid boxing if not enabled
            {
                this.Logger.LogInformation("[{MethodName}] Processed #{MessageCount} run messages: {RunId}", nameof(InvokeAsync), messageCount, run.Id);
            }
        }
        while (RunStatus.Completed != run.Status);

        this.Logger.LogInformation("[{MethodName}] Completed run: {RunId}", nameof(InvokeAsync), run.Id);

        // Local function to assist in run polling (participates in method closure).
        async Task PollRunStatusAsync()
        {
            this.Logger.LogInformation("[{MethodName}] Polling run status: {RunId}", nameof(PollRunStatusAsync), run.Id);

            int count = 0;

            do
            {
                // Reduce polling frequency after a couple attempts
                await Task.Delay(count >= 2 ? pollingConfiguration.RunPollingInterval : pollingConfiguration.RunPollingBackoff, cancellationToken).ConfigureAwait(false);
                ++count;

#pragma warning disable CA1031 // Do not catch general exception types
                try
                {
                    run = await this._client.GetRunAsync(this._threadId, run.Id, cancellationToken).ConfigureAwait(false);
                }
                catch
                {
                    // Retry anyway..
                }
#pragma warning restore CA1031 // Do not catch general exception types
            }
            while (s_pollingStatuses.Contains(run.Status));

            this.Logger.LogInformation("[{MethodName}] Run status is {RunStatus}: {RunId}", nameof(PollRunStatusAsync), run.Status, run.Id);
        }

        // Local function to capture kernel function state for further processing (participates in method closure).
        IEnumerable<FunctionCallContent> ParseFunctionStep(OpenAIAssistantAgent agent, RunStep step)
        {
            if (step.Status == RunStepStatus.InProgress && step.Type == RunStepType.ToolCalls)
            {
                foreach (RunStepToolCall toolCall in step.Details.ToolCalls)
                {
                    var nameParts = FunctionName.Parse(toolCall.FunctionName, FunctionDelimiter);

                    KernelArguments functionArguments = [];
                    if (!string.IsNullOrWhiteSpace(toolCall.FunctionArguments))
                    {
                        Dictionary<string, object> arguments = JsonSerializer.Deserialize<Dictionary<string, object>>(toolCall.FunctionArguments)!;
                        foreach (var argumentKvp in arguments)
                        {
                            functionArguments[argumentKvp.Key] = argumentKvp.Value.ToString();
                        }
                    }

                    var content = new FunctionCallContent(nameParts.Name, nameParts.PluginName, toolCall.ToolCallId, functionArguments);

                    functionSteps.Add(toolCall.ToolCallId, content);

                    yield return content;
                }
            }
        }
    }

    /// <inheritdoc/>
    protected override async IAsyncEnumerable<ChatMessageContent> GetHistoryAsync([EnumeratorCancellation] CancellationToken cancellationToken)
    {
        await foreach (ThreadMessage message in this._client.GetMessagesAsync(this._threadId, ListOrder.NewestFirst, cancellationToken).ConfigureAwait(false))
        {
            AuthorRole role = new(message.Role.ToString());

            string? assistantName = null;
            if (!string.IsNullOrWhiteSpace(message.AssistantId) &&
                !this._agentNames.TryGetValue(message.AssistantId, out assistantName))
            {
                Assistant assistant = await this._client.GetAssistantAsync(message.AssistantId).ConfigureAwait(false); // %%% CANCEL TOKEN
                if (!string.IsNullOrWhiteSpace(assistant.Name))
                {
                    this._agentNames.Add(assistant.Id, assistant.Name);
                }
            }

            assistantName ??= message.AssistantId;

            foreach (MessageContent itemContent in message.Content)
            {
                ChatMessageContent? content = null;

                if (!string.IsNullOrEmpty(itemContent.Text))
                {
                    content = GenerateTextMessageContent(assistantName, role, itemContent);
                }
                // Process image content
                else if (itemContent.ImageFileId != null)
                {
                    content = GenerateImageFileContent(assistantName, role, itemContent);
                }

                if (content is not null)
                {
                    yield return content;
                }
            }
        }
    }

    private static AnnotationContent GenerateAnnotationContent(TextAnnotation annotation)
    {
        string? fileId = null;

        if (string.IsNullOrEmpty(annotation.OutputFileId))
        {
            fileId = annotation.OutputFileId;
        }
        else if (string.IsNullOrEmpty(annotation.InputFileId))
        {
            fileId = annotation.InputFileId;
        }

        return
            new()
            {
                Quote = annotation.TextToReplace,
                StartIndex = annotation.StartIndex,
                EndIndex = annotation.EndIndex,
                FileId = fileId,
            };
    }

    private static ChatMessageContent GenerateImageFileContent(string agentName, AuthorRole role, MessageContent contentImage)
    {
        return
            new ChatMessageContent(
                role,
                [
                    new FileReferenceContent(contentImage.ImageFileId)
                ])
            {
                AuthorName = agentName,
            };
    }

    private static ChatMessageContent? GenerateTextMessageContent(string agentName, AuthorRole role, MessageContent contentMessage)
    {
        ChatMessageContent? messageContent = null;

        string textContent = contentMessage.Text.Trim();

        if (!string.IsNullOrWhiteSpace(textContent))
        {
            messageContent =
                new(role, textContent)
                {
                    AuthorName = agentName
                };

            foreach (TextAnnotation annotation in contentMessage.TextAnnotations)
            {
                messageContent.Items.Add(GenerateAnnotationContent(annotation));
            }
        }

        return messageContent;
    }

    private static ChatMessageContent GenerateCodeInterpreterContent(string agentName, string code)
    {
        return
            new ChatMessageContent(
                AuthorRole.Tool,
                [
                    new TextContent(code)
                ])
            {
                AuthorName = agentName,
            };
    }

    private static ChatMessageContent GenerateFunctionCallContent(string agentName, FunctionCallContent[] functionSteps)
    {
        ChatMessageContent functionCallContent = new(AuthorRole.Tool, content: null)
        {
            AuthorName = agentName
        };

        functionCallContent.Items.AddRange(functionSteps);

        return functionCallContent;
    }

    private static ChatMessageContent GenerateFunctionResultContent(string agentName, FunctionCallContent functionStep, string result)
    {
        ChatMessageContent functionCallContent = new(AuthorRole.Tool, content: null)
        {
            AuthorName = agentName
        };

        functionCallContent.Items.Add(
            new FunctionResultContent(
                functionStep.FunctionName,
                functionStep.PluginName,
                functionStep.Id,
                result));

        return functionCallContent;
    }

    private static Task<FunctionResultContent>[] ExecuteFunctionSteps(OpenAIAssistantAgent agent, FunctionCallContent[] functionSteps, CancellationToken cancellationToken)
    {
        Task<FunctionResultContent>[] functionTasks = new Task<FunctionResultContent>[functionSteps.Length];

        for (int index = 0; index < functionSteps.Length; ++index)
        {
            functionTasks[index] = functionSteps[index].InvokeAsync(agent.Kernel, cancellationToken);
        }

        return functionTasks;
    }

    private static ToolOutput[] GenerateToolOutputs(FunctionResultContent[] functionResults)
    {
        ToolOutput[] toolOutputs = new ToolOutput[functionResults.Length];

        for (int index = 0; index < functionResults.Length; ++index)
        {
            FunctionResultContent functionResult = functionResults[index];

            object resultValue = (functionResult.Result as FunctionResult)?.GetValue<object>() ?? string.Empty;

            if (resultValue is not string textResult)
            {
                textResult = JsonSerializer.Serialize(resultValue);
            }

            toolOutputs[index] = new ToolOutput(functionResult.CallId, textResult!);
        }

        return toolOutputs;
    }

    private async Task<ThreadMessage?> RetrieveMessageAsync(string messageId, CancellationToken cancellationToken)
    {
        ThreadMessage? message = null;

        bool retry = false;
        int count = 0;
        do
        {
            try
            {
                message = await this._client.GetMessageAsync(this._threadId, messageId, cancellationToken).ConfigureAwait(false);
            }
            catch (RequestFailedException exception)
            {
                // Step has provided the message-id.  Retry on of NotFound/404 exists.
                // Extremely rarely there might be a synchronization issue between the
                // assistant response and message-service.
                retry = exception.Status == (int)HttpStatusCode.NotFound && count < 3;
            }

            if (retry)
            {
                await Task.Delay(pollingConfiguration.MessageSynchronizationDelay, cancellationToken).ConfigureAwait(false);
            }

            ++count;
        }
        while (retry);

        return message;
    }
}
