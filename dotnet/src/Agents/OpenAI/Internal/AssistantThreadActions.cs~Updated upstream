// Copyright (c) Microsoft. All rights reserved.
using System;
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

namespace Microsoft.SemanticKernel.Agents.OpenAI.Internal;

/// <summary>
/// Actions associated with an Open Assistant thread.
/// </summary>
internal static class AssistantThreadActions
{
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

    /// <summary>
    /// Create a new assistant thread.
    /// </summary>
    /// <param name="client">The assistant client</param>
    /// <param name="options">The options for creating the thread</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The thread identifier</returns>
    public static async Task<string> CreateThreadAsync(AssistantClient client, OpenAIThreadCreationOptions? options, CancellationToken cancellationToken = default)
    {
        ThreadCreationOptions createOptions =
            new()
            {
                ToolResources = AssistantToolResourcesFactory.GenerateToolResources(options?.VectorStoreId, options?.CodeInterpreterFileIds),
            };

        if (options?.Messages is not null)
        {
            foreach (ChatMessageContent message in options.Messages)
            {
                ThreadInitializationMessage threadMessage = new(
                    role: message.Role == AuthorRole.User ? MessageRole.User : MessageRole.Assistant,
                    content: AssistantMessageFactory.GetMessageContents(message));
                createOptions.InitialMessages.Add(threadMessage);
            }
        }

        if (options?.Metadata != null)
        {
            foreach (KeyValuePair<string, string> item in options.Metadata)
            {
                createOptions.Metadata[item.Key] = item.Value;
            }
        }

        AssistantThread thread = await client.CreateThreadAsync(createOptions, cancellationToken).ConfigureAwait(false);

        return thread.Id;
    }

    /// <summary>
    /// Create a message in the specified thread.
    /// </summary>
    /// <param name="client">The assistant client</param>
    /// <param name="threadId">The thread identifier</param>
    /// <param name="message">The message to add</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <throws><see cref="KernelException"/> if a system message is present, without taking any other action</throws>
    public static async Task CreateMessageAsync(AssistantClient client, string threadId, ChatMessageContent message, CancellationToken cancellationToken)
    {
        if (message.Items.Any(i => i is FunctionCallContent))
        {
            return;
        }

        MessageCreationOptions options = AssistantMessageFactory.CreateOptions(message);

        await client.CreateMessageAsync(
            threadId,
            message.Role == AuthorRole.User ? MessageRole.User : MessageRole.Assistant,
            AssistantMessageFactory.GetMessageContents(message),
            options,
            cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Retrieves the thread messages.
    /// </summary>
    /// <param name="client">The assistant client</param>
    /// <param name="threadId">The thread identifier</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of messages.</returns>
    public static async IAsyncEnumerable<ChatMessageContent> GetMessagesAsync(AssistantClient client, string threadId, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        Dictionary<string, string?> agentNames = []; // Cache agent names by their identifier

        await foreach (PageResult<ThreadMessage> page in client.GetMessagesAsync(threadId, new() { Order = ListOrder.NewestFirst }, cancellationToken).ConfigureAwait(false))
        {
            foreach (var message in page.Values)
            foreach (ThreadMessage message in page.Values)
            {
                AuthorRole role = new(message.Role.ToString());

                string? assistantName = null;
                if (!string.IsNullOrWhiteSpace(message.AssistantId) &&
                    !agentNames.TryGetValue(message.AssistantId, out assistantName))
                {
                    Assistant assistant = await client.GetAssistantAsync(message.AssistantId, cancellationToken).ConfigureAwait(false);
                    if (!string.IsNullOrWhiteSpace(assistant.Name))
                    {
                        agentNames.Add(assistant.Id, assistant.Name);
                    }
                }

                assistantName ??= message.AssistantId;

                ChatMessageContent content = GenerateMessageContent(assistantName, message);

                if (content.Items.Count > 0)
                {
                    yield return content;
                }
            }
        }
    }

    /// <summary>
    /// Invoke the assistant on the specified thread.
    /// In the enumeration returned by this method, a message is considered visible if it is intended to be displayed to the user.
    /// Example of a non-visible message is function-content for functions that are automatically executed.
    /// </summary>
    /// <param name="agent">The assistant agent to interact with the thread.</param>
    /// <param name="client">The assistant client</param>
    /// <param name="threadId">The thread identifier</param>
    /// <param name="invocationOptions">Options to utilize for the invocation</param>
    /// <param name="logger">The logger to utilize (might be agent or channel scoped)</param>
    /// <param name="kernel">The <see cref="Kernel"/> plugins and other state.</param>
    /// <param name="arguments">Optional arguments to pass to the agents's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of messages.</returns>
    /// <remarks>
    /// The `arguments` parameter is not currently used by the agent, but is provided for future extensibility.
    /// </remarks>
    public static async IAsyncEnumerable<(bool IsVisible, ChatMessageContent Message)> InvokeAsync(
        OpenAIAssistantAgent agent,
        AssistantClient client,
        string threadId,
        OpenAIAssistantInvocationOptions? invocationOptions,
        ILogger logger,
        Kernel kernel,
        KernelArguments? arguments,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (agent.IsDeleted)
        {
            throw new KernelException($"Agent Failure - {nameof(OpenAIAssistantAgent)} agent is deleted: {agent.Id}.");
        }

        logger.LogOpenAIAssistantCreatingRun(nameof(InvokeAsync), threadId);

        ToolDefinition[]? tools = [.. agent.Tools, .. kernel.Plugins.SelectMany(p => p.Select(f => f.ToToolDefinition(p.Name)))];

        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(agent.Definition, invocationOptions);

        options.ToolsOverride.AddRange(tools);

        ThreadRun run = await client.CreateRunAsync(threadId, agent.Id, options, cancellationToken).ConfigureAwait(false);

        logger.LogOpenAIAssistantCreatedRun(nameof(InvokeAsync), run.Id, threadId);

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

            List<RunStep> steps = [];
            await foreach (var page in client.GetRunStepsAsync(run).ConfigureAwait(false))
            {
                steps.AddRange(page.Values);
            };
            IReadOnlyList<RunStep> steps = await GetRunStepsAsync(client, run).ConfigureAwait(false);

            // Is tool action required?
            if (run.Status == RunStatus.RequiresAction)
            {
                logger.LogOpenAIAssistantProcessingRunSteps(nameof(InvokeAsync), run.Id, threadId);

                // Execute functions in parallel and post results at once.
                FunctionCallContent[] activeFunctionSteps = steps.SelectMany(step => ParseFunctionStep(agent, step)).ToArray();
                if (activeFunctionSteps.Length > 0)
                {
                    // Emit function-call content
                    yield return (IsVisible: false, Message: GenerateFunctionCallContent(agent.GetName(), activeFunctionSteps));

                    // Invoke functions for each tool-step
                    IEnumerable<Task<FunctionResultContent>> functionResultTasks = ExecuteFunctionSteps(agent, activeFunctionSteps, cancellationToken);
                FunctionCallContent[] functionCalls = steps.SelectMany(step => ParseFunctionStep(agent, step)).ToArray();
                // Capture function-call for message processing
                foreach (FunctionCallContent functionCall in functionCalls)
                {
                    functionSteps.Add(functionCall.Id!, functionCall);
                }
                if (functionCalls.Length > 0)
                {
                    // Emit function-call content
                    yield return (IsVisible: false, Message: GenerateFunctionCallContent(agent.GetName(), functionCalls));

                    // Invoke functions for each tool-step
                    IEnumerable<Task<FunctionResultContent>> functionResultTasks = ExecuteFunctionSteps(agent, functionCalls, cancellationToken);

                    // Block for function results
                    FunctionResultContent[] functionResults = await Task.WhenAll(functionResultTasks).ConfigureAwait(false);

                    // Process tool output
                    ToolOutput[] toolOutputs = GenerateToolOutputs(functionResults);

                    await client.SubmitToolOutputsToRunAsync(threadId, run.Id, toolOutputs, cancellationToken).ConfigureAwait(false);
                }

                logger.LogOpenAIAssistantProcessedRunSteps(nameof(InvokeAsync), activeFunctionSteps.Length, run.Id, threadId);
                logger.LogOpenAIAssistantProcessedRunSteps(nameof(InvokeAsync), functionCalls.Length, run.Id, threadId);
            }

            // Enumerate completed messages
            logger.LogOpenAIAssistantProcessingRunMessages(nameof(InvokeAsync), run.Id, threadId);

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
                        bool isVisible = false;
                        ChatMessageContent? content = null;

                        // Process code-interpreter content
                        if (toolCall.ToolKind == RunStepToolCallKind.CodeInterpreter)
                        {
                            content = GenerateCodeInterpreterContent(agent.GetName(), toolCall.CodeInterpreterInput);
                            isVisible = true;
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

                            yield return (isVisible, Message: content);
                        }
                    }
                }
                else if (completedStep.Type == RunStepType.MessageCreation)
                {
                    // Retrieve the message
                    ThreadMessage? message = await RetrieveMessageAsync(completedStep.Details.CreatedMessageId, cancellationToken).ConfigureAwait(false);
                    ThreadMessage? message = await RetrieveMessageAsync(client, threadId, completedStep.Details.CreatedMessageId, agent.PollingOptions.MessageSynchronizationDelay, cancellationToken).ConfigureAwait(false);

                    if (message is not null)
                    {
                        ChatMessageContent content = GenerateMessageContent(agent.GetName(), message);

                        if (content.Items.Count > 0)
                        {
                            ++messageCount;

                            yield return (IsVisible: true, Message: content);
                        }
                    }
                }

                processedStepIds.Add(completedStep.Id);
            }

            logger.LogOpenAIAssistantProcessedRunMessages(nameof(InvokeAsync), messageCount, run.Id, threadId);
        }
        while (RunStatus.Completed != run.Status);

        logger.LogOpenAIAssistantCompletedRun(nameof(InvokeAsync), run.Id, threadId);

        // Local function to assist in run polling (participates in method closure).
        async Task PollRunStatusAsync()
        {
            logger.LogOpenAIAssistantPollingRunStatus(nameof(PollRunStatusAsync), run.Id, threadId);

            int count = 0;

            do
            {
                // Reduce polling frequency after a couple attempts
                await Task.Delay(agent.PollingOptions.GetPollingInterval(count), cancellationToken).ConfigureAwait(false);
                ++count;

#pragma warning disable CA1031 // Do not catch general exception types
                try
                {
                    run = await client.GetRunAsync(threadId, run.Id, cancellationToken).ConfigureAwait(false);
                }
                catch
                {
                    // Retry anyway..
                }
#pragma warning restore CA1031 // Do not catch general exception types
            }
            while (s_pollingStatuses.Contains(run.Status));

            logger.LogOpenAIAssistantPolledRunStatus(nameof(PollRunStatusAsync), run.Status, run.Id, threadId);
        }

        // Local function to capture kernel function state for further processing (participates in method closure).
        IEnumerable<FunctionCallContent> ParseFunctionStep(OpenAIAssistantAgent agent, RunStep step)
        {
            if (step.Status == RunStepStatus.InProgress && step.Type == RunStepType.ToolCalls)
            {
                foreach (RunStepToolCall toolCall in step.Details.ToolCalls)
                {
                    var nameParts = FunctionName.Parse(toolCall.FunctionName);

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

        async Task<ThreadMessage?> RetrieveMessageAsync(string messageId, CancellationToken cancellationToken)
        {
            ThreadMessage? message = null;

            bool retry = false;
            int count = 0;
            do
            {
                try
                {
                    message = await client.GetMessageAsync(threadId, messageId, cancellationToken).ConfigureAwait(false);
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
                    await Task.Delay(agent.PollingOptions.MessageSynchronizationDelay, cancellationToken).ConfigureAwait(false);
                }

                ++count;
            }
            while (retry);

            return message;
        }
    }

    /// <summary>
    /// Invoke the assistant on the specified thread using streaming.
    /// </summary>
    /// <param name="agent">The assistant agent to interact with the thread.</param>
    /// <param name="client">The assistant client</param>
    /// <param name="threadId">The thread identifier</param>
    /// <param name="messages">The receiver for the completed messages generated</param>
    /// <param name="invocationOptions">Options to utilize for the invocation</param>
    /// <param name="logger">The logger to utilize (might be agent or channel scoped)</param>
    /// <param name="kernel">The <see cref="Kernel"/> plugins and other state.</param>
    /// <param name="arguments">Optional arguments to pass to the agents's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of messages.</returns>
    /// <remarks>
    /// The `arguments` parameter is not currently used by the agent, but is provided for future extensibility.
    /// </remarks>
    public static async IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(
        OpenAIAssistantAgent agent,
        AssistantClient client,
        string threadId,
        IList<ChatMessageContent> messages,
        OpenAIAssistantInvocationOptions? invocationOptions,
        ILogger logger,
        Kernel kernel,
        KernelArguments? arguments,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (agent.IsDeleted)
        {
            throw new KernelException($"Agent Failure - {nameof(OpenAIAssistantAgent)} agent is deleted: {agent.Id}.");
        }

        logger.LogOpenAIAssistantCreatingRun(nameof(InvokeAsync), threadId);

        ToolDefinition[]? tools = [.. agent.Tools, .. kernel.Plugins.SelectMany(p => p.Select(f => f.ToToolDefinition(p.Name)))];

        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(agent.Definition, invocationOptions);

        options.ToolsOverride.AddRange(tools);

        // Evaluate status and process steps and messages, as encountered.
        HashSet<string> processedStepIds = [];
        HashSet<string> messageIds = [];

        ThreadRun? run = null;
        IAsyncEnumerable<StreamingUpdate> asyncUpdates = client.CreateRunStreamingAsync(threadId, agent.Id, options, cancellationToken);
        do
        {
            messageIds.Clear();

            await foreach (StreamingUpdate update in asyncUpdates.ConfigureAwait(false))
            {
                if (update is RunUpdate runUpdate)
                {
                    run = runUpdate.Value;

                    logger.LogOpenAIAssistantCreatedRun(nameof(InvokeAsync), run.Id, threadId);
                }
                else if (update is MessageContentUpdate contentUpdate)
                {
                    messageIds.Add(contentUpdate.MessageId);
                    yield return GenerateStreamingMessageContent(agent.GetName(), contentUpdate);
                }
            }

            if (run == null)
            {
                throw new KernelException($"Agent Failure - Run not created for thread: ${threadId}");
            }

            // Is in terminal state?
            if (s_terminalStatuses.Contains(run.Status))
            {
                throw new KernelException($"Agent Failure - Run terminated: {run.Status} [{run.Id}]: {run.LastError?.Message ?? "Unknown"}");
            }

            if (run.Status == RunStatus.RequiresAction)
            {
                IReadOnlyList<RunStep> steps = await GetRunStepsAsync(client, run).ConfigureAwait(false);

                // Execute functions in parallel and post results at once.
                FunctionCallContent[] functionCalls = steps.SelectMany(step => ParseFunctionStep(agent, step)).ToArray();
                if (functionCalls.Length > 0)
                {
                    // Emit function-call content
                    messages.Add(GenerateFunctionCallContent(agent.GetName(), functionCalls));

                    // Invoke functions for each tool-step
                    IEnumerable<Task<FunctionResultContent>> functionResultTasks = ExecuteFunctionSteps(agent, functionCalls, cancellationToken);

                    // Block for function results
                    FunctionResultContent[] functionResults = await Task.WhenAll(functionResultTasks).ConfigureAwait(false);

                    // Process tool output
                    ToolOutput[] toolOutputs = GenerateToolOutputs(functionResults);
                    asyncUpdates = client.SubmitToolOutputsToRunStreamingAsync(run, toolOutputs);

                    messages.Add(GenerateFunctionResultsContent(agent.GetName(), functionResults));
                }
            }

            if (messageIds.Count > 0)
            {
                logger.LogOpenAIAssistantProcessingRunMessages(nameof(InvokeAsync), run!.Id, threadId);

                foreach (string messageId in messageIds)
                {
                    ThreadMessage? message = await RetrieveMessageAsync(client, threadId, messageId, agent.PollingOptions.MessageSynchronizationDelay, cancellationToken).ConfigureAwait(false);

                    if (message != null)
                    {
                        ChatMessageContent content = GenerateMessageContent(agent.GetName(), message);
                        messages.Add(content);
                    }
                }

                logger.LogOpenAIAssistantProcessedRunMessages(nameof(InvokeAsync), messageIds.Count, run!.Id, threadId);
            }
        }
        while (run?.Status != RunStatus.Completed);

        logger.LogOpenAIAssistantCompletedRun(nameof(InvokeAsync), run?.Id ?? "Failed", threadId);
    }

    private static async Task<IReadOnlyList<RunStep>> GetRunStepsAsync(AssistantClient client, ThreadRun run)
    {
        List<RunStep> steps = [];

        await foreach (PageResult<RunStep> page in client.GetRunStepsAsync(run).ConfigureAwait(false))
        {
            steps.AddRange(page.Values);
        };

        return steps;
    }

    private static ChatMessageContent GenerateMessageContent(string? assistantName, ThreadMessage message)
    {
        AuthorRole role = new(message.Role.ToString());

        ChatMessageContent content =
            new(role, content: null)
            {
                AuthorName = assistantName,
            };

        foreach (MessageContent itemContent in message.Content)
        {
            // Process text content
            if (!string.IsNullOrEmpty(itemContent.Text))
            {
                content.Items.Add(new TextContent(itemContent.Text));

                foreach (TextAnnotation annotation in itemContent.TextAnnotations)
                {
                    content.Items.Add(GenerateAnnotationContent(annotation));
                }
            }
            // Process image content
            else if (itemContent.ImageFileId != null)
            {
                content.Items.Add(new FileReferenceContent(itemContent.ImageFileId));
            }
        }

        return content;
    }

    private static StreamingChatMessageContent GenerateStreamingMessageContent(string? assistantName, MessageContentUpdate update)
    {
        StreamingChatMessageContent content =
            new(AuthorRole.Assistant, content: null)
            {
                AuthorName = assistantName,
            };

        // Process text content
        if (!string.IsNullOrEmpty(update.Text))
        {
            content.Items.Add(new StreamingTextContent(update.Text));
        }
        // Process image content
        else if (update.ImageFileId != null)
        {
            content.Items.Add(new StreamingFileReferenceContent(update.ImageFileId));
        }
        // Process annotations
        else if (update.TextAnnotation != null)
        {
            content.Items.Add(GenerateStreamingAnnotationContent(update.TextAnnotation));
        }

        if (update.Role.HasValue && update.Role.Value != MessageRole.User)
        {
            content.Role = new(update.Role.Value.ToString());
        }

        return content;
    }

    private static AnnotationContent GenerateAnnotationContent(TextAnnotation annotation)
    {
        string? fileId = null;

        if (!string.IsNullOrEmpty(annotation.OutputFileId))
        {
            fileId = annotation.OutputFileId;
        }
        else if (!string.IsNullOrEmpty(annotation.InputFileId))
        {
            fileId = annotation.InputFileId;
        }

        return
            new()
            new(annotation.TextToReplace)
            {
                Quote = annotation.TextToReplace,
                StartIndex = annotation.StartIndex,
                EndIndex = annotation.EndIndex,
                FileId = fileId,
            };
    }

    private static StreamingAnnotationContent GenerateStreamingAnnotationContent(TextAnnotationUpdate annotation)
    {
        string? fileId = null;

        if (!string.IsNullOrEmpty(annotation.OutputFileId))
        {
            fileId = annotation.OutputFileId;
        }
        else if (!string.IsNullOrEmpty(annotation.InputFileId))
        {
            fileId = annotation.InputFileId;
        }

        return
            new(annotation.TextToReplace)
            {
                StartIndex = annotation.StartIndex ?? 0,
                EndIndex = annotation.EndIndex ?? 0,
                FileId = fileId,
            };
    }

    private static ChatMessageContent GenerateCodeInterpreterContent(string agentName, string pythonCode)
    {
        return
            new ChatMessageContent(
                AuthorRole.Assistant,
                [
                    new TextContent(pythonCode)
                ])
            {
                AuthorName = agentName,
                Metadata = new Dictionary<string, object?> { { OpenAIAssistantAgent.CodeInterpreterMetadataKey, true } },
            };
    }

    private static ChatMessageContent GenerateFunctionCallContent(string agentName, FunctionCallContent[] functionSteps)
    private static IEnumerable<FunctionCallContent> ParseFunctionStep(OpenAIAssistantAgent agent, RunStep step)
    {
        if (step.Status == RunStepStatus.InProgress && step.Type == RunStepType.ToolCalls)
        {
            foreach (RunStepToolCall toolCall in step.Details.ToolCalls)
            {
                (FunctionName nameParts, KernelArguments functionArguments) = ParseFunctionCall(toolCall.FunctionName, toolCall.FunctionArguments);

                FunctionCallContent content = new(nameParts.Name, nameParts.PluginName, toolCall.ToolCallId, functionArguments);

                yield return content;
            }
        }
    }

    private static (FunctionName functionName, KernelArguments arguments) ParseFunctionCall(string functionName, string? functionArguments)
    {
        FunctionName nameParts = FunctionName.Parse(functionName);

        KernelArguments arguments = [];

        if (!string.IsNullOrWhiteSpace(functionArguments))
        {
            foreach (var argumentKvp in JsonSerializer.Deserialize<Dictionary<string, object>>(functionArguments!)!)
            {
                arguments[argumentKvp.Key] = argumentKvp.Value.ToString();
            }
        }

        return (nameParts, arguments);
    }

    private static ChatMessageContent GenerateFunctionCallContent(string agentName, IList<FunctionCallContent> functionCalls)
    {
        ChatMessageContent functionCallContent = new(AuthorRole.Tool, content: null)
        {
            AuthorName = agentName
        };

        functionCallContent.Items.AddRange(functionSteps);
        functionCallContent.Items.AddRange(functionCalls);

        return functionCallContent;
    }

    private static ChatMessageContent GenerateFunctionResultContent(string agentName, FunctionCallContent functionStep, string result)
    private static ChatMessageContent GenerateFunctionResultContent(string agentName, FunctionCallContent functionCall, string result)
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
                functionCall.FunctionName,
                functionCall.PluginName,
                functionCall.Id,
                result));

        return functionCallContent;
    }

    private static Task<FunctionResultContent>[] ExecuteFunctionSteps(OpenAIAssistantAgent agent, FunctionCallContent[] functionSteps, CancellationToken cancellationToken)
    {
        Task<FunctionResultContent>[] functionTasks = new Task<FunctionResultContent>[functionSteps.Length];

        for (int index = 0; index < functionSteps.Length; ++index)
        {
            functionTasks[index] = functionSteps[index].InvokeAsync(agent.Kernel, cancellationToken);
    private static ChatMessageContent GenerateFunctionResultsContent(string agentName, IList<FunctionResultContent> functionResults)
    {
        ChatMessageContent functionResultContent = new(AuthorRole.Tool, content: null)
        {
            AuthorName = agentName
        };

        foreach (FunctionResultContent functionResult in functionResults)
        {
            functionResultContent.Items.Add(
                new FunctionResultContent(
                    functionResult.FunctionName,
                    functionResult.PluginName,
                    functionResult.CallId,
                    functionResult.Result));
        }

        return functionResultContent;
    }

    private static Task<FunctionResultContent>[] ExecuteFunctionSteps(OpenAIAssistantAgent agent, FunctionCallContent[] functionCalls, CancellationToken cancellationToken)
    {
        Task<FunctionResultContent>[] functionTasks = new Task<FunctionResultContent>[functionCalls.Length];

        for (int index = 0; index < functionCalls.Length; ++index)
        {
            functionTasks[index] = functionCalls[index].InvokeAsync(agent.Kernel, cancellationToken);
        }

        return functionTasks;
    }

    private static Task<FunctionResultContent> ExecuteFunctionStep(OpenAIAssistantAgent agent, FunctionCallContent functionCall, CancellationToken cancellationToken)
    {
        return functionCall.InvokeAsync(agent.Kernel, cancellationToken);
    }

    private static ToolOutput[] GenerateToolOutputs(FunctionResultContent[] functionResults)
    {
        ToolOutput[] toolOutputs = new ToolOutput[functionResults.Length];

        for (int index = 0; index < functionResults.Length; ++index)
        {
            FunctionResultContent functionResult = functionResults[index];

            object resultValue = functionResult.Result ?? string.Empty;

            if (resultValue is not string textResult)
            {
                textResult = JsonSerializer.Serialize(resultValue);
            }

            toolOutputs[index] = new ToolOutput(functionResult.CallId, textResult!);
        }

        return toolOutputs;
    }

    private static async Task<ThreadMessage?> RetrieveMessageAsync(AssistantClient client, string threadId, string messageId, TimeSpan syncDelay, CancellationToken cancellationToken)
    {
        ThreadMessage? message = null;

        bool retry = false;
        int count = 0;
        do
        {
            try
            {
                message = await client.GetMessageAsync(threadId, messageId, cancellationToken).ConfigureAwait(false);
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
                await Task.Delay(syncDelay, cancellationToken).ConfigureAwait(false);
            }

            ++count;
        }
        while (retry);

        return message;
    }
}
