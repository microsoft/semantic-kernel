// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Azure;
using Azure.AI.OpenAI.Assistants;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// A <see cref="AgentChannel"/> specialization for use with <see cref="OpenAIAssistantAgent"/>.
/// </summary>
internal sealed class OpenAIAssistantChannel(AssistantsClient client, string threadId, OpenAIAssistantConfiguration.PollingConfiguration pollingConfiguration)
    : AgentChannel<OpenAIAssistantAgent>
{
    private const char FunctionDelimiter = '-';

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

    private readonly AssistantsClient _client = client;
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

            await this._client.CreateMessageAsync(
                this._threadId,
                message.Role.ToMessageRole(),
                message.Content,
                cancellationToken: cancellationToken).ConfigureAwait(false);
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

        CreateRunOptions options =
            new(agent.Id)
            {
                OverrideInstructions = agent.Instructions,
                OverrideTools = tools,
            };

        // Create run
        ThreadRun run = await this._client.CreateRunAsync(this._threadId, options, cancellationToken).ConfigureAwait(false);

        this.Logger.LogInformation("[{MethodName}] Created run: {RunId}", nameof(InvokeAsync), run.Id);

        // Evaluate status and process steps and messages, as encountered.
        HashSet<string> processedStepIds = [];
        Dictionary<string, KernelFunctionStep> functionSteps = [];

        do
        {
            // Poll run and steps until actionable
            PageableList<RunStep> steps = await PollRunStatusAsync().ConfigureAwait(false);

            // Is in terminal state?
            if (s_terminalStatuses.Contains(run.Status))
            {
                throw new KernelException($"Agent Failure - Run terminated: {run.Status} [{run.Id}]: {run.LastError?.Message ?? "Unknown"}");
            }

            // Is tool action required?
            if (run.Status == RunStatus.RequiresAction)
            {
                this.Logger.LogDebug("[{MethodName}] Processing run steps: {RunId}", nameof(InvokeAsync), run.Id);

                // Execute functions in parallel and post results at once.
                var functionTasks = steps.Data.SelectMany(step => ExecuteStep(agent, step, cancellationToken)).ToArray();
                if (functionTasks.Length > 0)
                {
                    // Emit function-call content
                    yield return GenerateFunctionCallContent(agent.GetName(), functionTasks);

                    // Capture function-step for FunctionResultContent generation
                    foreach (KernelFunctionTask task in functionTasks)
                    {
                        functionSteps.Add(task.FunctionStep.ToolCallId, task.FunctionStep);
                    }

                    // Block for function results and process
                    ToolOutput[]? results = await Task.WhenAll(functionTasks.Select(t => t.FunctionTask)).ConfigureAwait(false);

                    await this._client.SubmitToolOutputsToRunAsync(run, results, cancellationToken).ConfigureAwait(false);
                }

                if (this.Logger.IsEnabled(LogLevel.Information)) // Avoid boxing if not enabled
                {
                    this.Logger.LogInformation("[{MethodName}] Processed #{MessageCount} run steps: {RunId}", nameof(InvokeAsync), functionTasks.Length, run.Id);
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
                if (completedStep.Type.Equals(RunStepType.ToolCalls))
                {
                    RunStepToolCallDetails toolCallDetails = (RunStepToolCallDetails)completedStep.StepDetails;

                    foreach (RunStepToolCall toolCall in toolCallDetails.ToolCalls)
                    {
                        ChatMessageContent? content = null;

                        // Process code-interpreter content
                        if (toolCall is RunStepCodeInterpreterToolCall toolCodeInterpreter)
                        {
                            content = GenerateCodeInterpreterContent(agent.GetName(), toolCodeInterpreter);
                        }
                        // Process function result content
                        else if (toolCall is RunStepFunctionToolCall toolFunction)
                        {
                            KernelFunctionStep functionStep = functionSteps[toolFunction.Id]; // Function step always captured on invocation
                            content = GenerateFunctionResultContent(agent.GetName(), functionStep, toolFunction.Output);
                        }

                        if (content is not null)
                        {
                            ++messageCount;

                            yield return content;
                        }
                    }
                }
                else if (completedStep.Type.Equals(RunStepType.MessageCreation))
                {
                    RunStepMessageCreationDetails messageCreationDetails = (RunStepMessageCreationDetails)completedStep.StepDetails;

                    // Retrieve the message
                    ThreadMessage? message = await this.RetrieveMessageAsync(messageCreationDetails, cancellationToken).ConfigureAwait(false);

                    if (message is not null)
                    {
                        AuthorRole role = new(message.Role.ToString());

                        foreach (MessageContent itemContent in message.ContentItems)
                        {
                            ChatMessageContent? content = null;

                            // Process text content
                            if (itemContent is MessageTextContent contentMessage)
                            {
                                content = GenerateTextMessageContent(agent.GetName(), role, contentMessage);
                            }
                            // Process image content
                            else if (itemContent is MessageImageFileContent contentImage)
                            {
                                content = GenerateImageFileContent(agent.GetName(), role, contentImage);
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
        async Task<PageableList<RunStep>> PollRunStatusAsync()
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

            return await this._client.GetRunStepsAsync(run, cancellationToken: cancellationToken).ConfigureAwait(false);
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
            foreach (ThreadMessage message in messages)
            {
                AuthorRole role = new(message.Role.ToString());

                string? assistantName = null;
                if (!string.IsNullOrWhiteSpace(message.AssistantId) &&
                    !this._agentNames.TryGetValue(message.AssistantId, out assistantName))
                {
                    Assistant assistant = await this._client.GetAssistantAsync(message.AssistantId, cancellationToken).ConfigureAwait(false);
                    if (!string.IsNullOrWhiteSpace(assistant.Name))
                    {
                        this._agentNames.Add(assistant.Id, assistant.Name);
                    }
                }

                assistantName ??= message.AssistantId;

                foreach (MessageContent item in message.ContentItems)
                {
                    ChatMessageContent? content = null;

                    if (item is MessageTextContent contentMessage)
                    {
                        content = GenerateTextMessageContent(assistantName, role, contentMessage);
                    }
                    else if (item is MessageImageFileContent contentImage)
                    {
                        content = GenerateImageFileContent(assistantName, role, contentImage);
                    }

                    if (content is not null)
                    {
                        yield return content;
                    }
                }

                lastId = message.Id;
            }
        }
        while (messages.HasMore);
    }

    private static AnnotationContent GenerateAnnotationContent(MessageTextAnnotation annotation)
    {
        string? fileId = null;
        if (annotation is MessageTextFileCitationAnnotation citationAnnotation)
        {
            fileId = citationAnnotation.FileId;
        }
        else if (annotation is MessageTextFilePathAnnotation pathAnnotation)
        {
            fileId = pathAnnotation.FileId;
        }

        return
            new()
            {
                Quote = annotation.Text,
                StartIndex = annotation.StartIndex,
                EndIndex = annotation.EndIndex,
                FileId = fileId,
            };
    }

    private static ChatMessageContent GenerateImageFileContent(string agentName, AuthorRole role, MessageImageFileContent contentImage)
    {
        return
            new ChatMessageContent(
                role,
                [
                    new FileReferenceContent(contentImage.FileId)
                ])
            {
                AuthorName = agentName,
            };
    }

    private static ChatMessageContent? GenerateTextMessageContent(string agentName, AuthorRole role, MessageTextContent contentMessage)
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

            foreach (MessageTextAnnotation annotation in contentMessage.Annotations)
            {
                messageContent.Items.Add(GenerateAnnotationContent(annotation));
            }
        }

        return messageContent;
    }

    private static ChatMessageContent GenerateCodeInterpreterContent(string agentName, RunStepCodeInterpreterToolCall contentCodeInterpreter)
    {
        return
            new ChatMessageContent(
                AuthorRole.Tool,
                [
                    new TextContent(contentCodeInterpreter.Input)
                ])
            {
                AuthorName = agentName,
            };
    }

    private static ChatMessageContent GenerateFunctionCallContent(string agentName, KernelFunctionTask[] functionTasks)
    {
        ChatMessageContent functionCallContent = new(AuthorRole.Tool, content: null)
        {
            AuthorName = agentName
        };

        functionCallContent.Items.AddRange(
            functionTasks.Select(
                t =>
                    new FunctionCallContent(
                        t.FunctionStep.Function.Name,
                        t.FunctionStep.Function.PluginName,
                        t.FunctionStep.ToolCallId,
                        t.FunctionStep.Arguments)));

        return functionCallContent;
    }

    private static ChatMessageContent GenerateFunctionResultContent(string agentName, KernelFunctionStep functionStep, string result)
    {
        ChatMessageContent functionCallContent = new(AuthorRole.Tool, content: null)
        {
            AuthorName = agentName
        };

        functionCallContent.Items.Add(
            new FunctionResultContent(
                functionStep.Function.Name,
                functionStep.Function.PluginName,
                functionStep.ToolCallId,
                result));

        return functionCallContent;
    }

    // Capture kernel function references for content processing
    private sealed record KernelFunctionStep(string ToolCallId, KernelFunction Function, KernelArguments Arguments);

    // Associate kernel function references with function execution task
    private sealed record KernelFunctionTask(KernelFunctionStep FunctionStep, Task<ToolOutput> FunctionTask);

    private static IEnumerable<KernelFunctionTask> ExecuteStep(OpenAIAssistantAgent agent, RunStep step, CancellationToken cancellationToken)
    {
        // Process all of the steps that require action
        if (step.Status == RunStepStatus.InProgress && step.StepDetails is RunStepToolCallDetails callDetails)
        {
            foreach (RunStepFunctionToolCall toolCall in callDetails.ToolCalls.OfType<RunStepFunctionToolCall>())
            {
                KernelFunctionStep functionStep = ParseFunctionStep(toolCall);

                // Yield function task
                yield return new(functionStep, ProcessFunctionStepAsync(functionStep));
            }
        }

        // Local function to capture kernel function state for further processing (participates in method closure).
        KernelFunctionStep ParseFunctionStep(RunStepFunctionToolCall functionDetails)
        {
            KernelFunction function = agent.Kernel.GetKernelFunction(functionDetails.Name, FunctionDelimiter);

            KernelArguments functionArguments = [];
            if (!string.IsNullOrWhiteSpace(functionDetails.Arguments))
            {
                Dictionary<string, object> arguments = JsonSerializer.Deserialize<Dictionary<string, object>>(functionDetails.Arguments)!;
                foreach (var argumentKvp in arguments)
                {
                    functionArguments[argumentKvp.Key] = argumentKvp.Value.ToString();
                }
            }

            return new(functionDetails.Id, function, functionArguments);
        }

        // Local function for processing the function-step (participates in method closure).
        async Task<ToolOutput> ProcessFunctionStepAsync(KernelFunctionStep functionStep)
        {
            FunctionResult functionResult = await functionStep.Function.InvokeAsync(agent.Kernel, functionStep.Arguments, cancellationToken).ConfigureAwait(false);

            object resultValue = functionResult.GetValue<object>() ?? string.Empty;

            if (resultValue is not string textResult)
            {
                textResult = JsonSerializer.Serialize(resultValue);
            }

            return new ToolOutput(functionStep.ToolCallId, textResult!);
        }
    }

    private async Task<ThreadMessage?> RetrieveMessageAsync(RunStepMessageCreationDetails detail, CancellationToken cancellationToken)
    {
        ThreadMessage? message = null;

        bool retry = false;
        int count = 0;
        do
        {
            try
            {
                message = await this._client.GetMessageAsync(this._threadId, detail.MessageCreation.MessageId, cancellationToken).ConfigureAwait(false);
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
