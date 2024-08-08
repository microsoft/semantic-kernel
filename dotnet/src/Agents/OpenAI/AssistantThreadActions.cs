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
/// Actions associated with an Open Assistant thread.
/// </summary>
internal static class AssistantThreadActions
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

    /// <summary>
    /// Create a message in the specified thread.
    /// </summary>
    /// <param name="client">The assistant client</param>
    /// <param name="threadId">The thread identifier</param>
    /// <param name="message">The message to add</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <throws><see cref="KernelException"/> if a system message is present, without taking any other action</throws>
    public static async Task CreateMessageAsync(AssistantsClient client, string threadId, ChatMessageContent message, CancellationToken cancellationToken)
    {
        if (message.Items.Any(i => i is FunctionCallContent))
        {
            return;
        }

        await client.CreateMessageAsync(
            threadId,
            message.Role.ToMessageRole(),
            message.Content,
            cancellationToken: cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Retrieves the thread messages.
    /// </summary>
    /// <param name="client">The assistant client</param>
    /// <param name="threadId">The thread identifier</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of messages.</returns>
    public static async IAsyncEnumerable<ChatMessageContent> GetMessagesAsync(AssistantsClient client, string threadId, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        Dictionary<string, string?> agentNames = []; // Cache agent names by their identifier

        PageableList<ThreadMessage> messages;

        string? lastId = null;
        do
        {
            messages = await client.GetMessagesAsync(threadId, limit: 100, ListSortOrder.Descending, after: lastId, null, cancellationToken).ConfigureAwait(false);
            foreach (ThreadMessage message in messages)
            {
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

                lastId = message.Id;
            }
        }
        while (messages.HasMore);
    }

    /// <summary>
    /// Invoke the assistant on the specified thread.
    /// </summary>
    /// <param name="agent">The assistant agent to interact with the thread.</param>
    /// <param name="client">The assistant client</param>
    /// <param name="threadId">The thread identifier</param>
    /// <param name="pollingConfiguration">Config to utilize when polling for run state.</param>
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
        AssistantsClient client,
        string threadId,
        OpenAIAssistantConfiguration.PollingConfiguration pollingConfiguration,
        ILogger logger,
        Kernel kernel,
        KernelArguments? arguments,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (agent.IsDeleted)
        {
            throw new KernelException($"Agent Failure - {nameof(OpenAIAssistantAgent)} agent is deleted: {agent.Id}.");
        }

        ToolDefinition[]? tools = [.. agent.Tools, .. kernel.Plugins.SelectMany(p => p.Select(f => f.ToToolDefinition(p.Name, FunctionDelimiter)))];

        logger.LogOpenAIAssistantCreatingRun(nameof(InvokeAsync), threadId);

        CreateRunOptions options =
            new(agent.Id)
            {
                OverrideInstructions = agent.Instructions,
                OverrideTools = tools,
            };

        // Create run
        ThreadRun run = await client.CreateRunAsync(threadId, options, cancellationToken).ConfigureAwait(false);

        logger.LogOpenAIAssistantCreatedRun(nameof(InvokeAsync), run.Id, threadId);

        // Evaluate status and process steps and messages, as encountered.
        HashSet<string> processedStepIds = [];
        Dictionary<string, FunctionCallContent> functionSteps = [];

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
                logger.LogOpenAIAssistantProcessingRunSteps(nameof(InvokeAsync), run.Id, threadId);

                // Execute functions in parallel and post results at once.
                FunctionCallContent[] activeFunctionSteps = steps.Data.SelectMany(step => ParseFunctionStep(agent, step)).ToArray();
                if (activeFunctionSteps.Length > 0)
                {
                    // Emit function-call content
                    yield return (IsVisible: false, Message: GenerateFunctionCallContent(agent.GetName(), activeFunctionSteps));

                    // Invoke functions for each tool-step
                    IEnumerable<Task<FunctionResultContent>> functionResultTasks = ExecuteFunctionSteps(agent, activeFunctionSteps, cancellationToken);

                    // Block for function results
                    FunctionResultContent[] functionResults = await Task.WhenAll(functionResultTasks).ConfigureAwait(false);

                    // Process tool output
                    ToolOutput[] toolOutputs = GenerateToolOutputs(functionResults);

                    await client.SubmitToolOutputsToRunAsync(run, toolOutputs, cancellationToken).ConfigureAwait(false);
                }

                logger.LogOpenAIAssistantProcessedRunSteps(nameof(InvokeAsync), activeFunctionSteps.Length, run.Id, threadId);
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
                if (completedStep.Type.Equals(RunStepType.ToolCalls))
                {
                    RunStepToolCallDetails toolCallDetails = (RunStepToolCallDetails)completedStep.StepDetails;

                    foreach (RunStepToolCall toolCall in toolCallDetails.ToolCalls)
                    {
                        bool isVisible = false;
                        ChatMessageContent? content = null;

                        // Process code-interpreter content
                        if (toolCall is RunStepCodeInterpreterToolCall toolCodeInterpreter)
                        {
                            content = GenerateCodeInterpreterContent(agent.GetName(), toolCodeInterpreter);
                            isVisible = true;
                        }
                        // Process function result content
                        else if (toolCall is RunStepFunctionToolCall toolFunction)
                        {
                            FunctionCallContent functionStep = functionSteps[toolFunction.Id]; // Function step always captured on invocation
                            content = GenerateFunctionResultContent(agent.GetName(), functionStep, toolFunction.Output);
                        }

                        if (content is not null)
                        {
                            ++messageCount;

                            yield return (isVisible, Message: content);
                        }
                    }
                }
                else if (completedStep.Type.Equals(RunStepType.MessageCreation))
                {
                    RunStepMessageCreationDetails messageCreationDetails = (RunStepMessageCreationDetails)completedStep.StepDetails;

                    // Retrieve the message
                    ThreadMessage? message = await RetrieveMessageAsync(messageCreationDetails, cancellationToken).ConfigureAwait(false);

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
        async Task<PageableList<RunStep>> PollRunStatusAsync()
        {
            logger.LogOpenAIAssistantPollingRunStatus(nameof(PollRunStatusAsync), run.Id, threadId);

            int count = 0;

            do
            {
                // Reduce polling frequency after a couple attempts
                await Task.Delay(count >= 2 ? pollingConfiguration.RunPollingInterval : pollingConfiguration.RunPollingBackoff, cancellationToken).ConfigureAwait(false);
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

            return await client.GetRunStepsAsync(run, cancellationToken: cancellationToken).ConfigureAwait(false);
        }

        // Local function to capture kernel function state for further processing (participates in method closure).
        IEnumerable<FunctionCallContent> ParseFunctionStep(OpenAIAssistantAgent agent, RunStep step)
        {
            if (step.Status == RunStepStatus.InProgress && step.StepDetails is RunStepToolCallDetails callDetails)
            {
                foreach (RunStepFunctionToolCall toolCall in callDetails.ToolCalls.OfType<RunStepFunctionToolCall>())
                {
                    var nameParts = FunctionName.Parse(toolCall.Name, FunctionDelimiter);

                    KernelArguments functionArguments = [];
                    if (!string.IsNullOrWhiteSpace(toolCall.Arguments))
                    {
                        Dictionary<string, object> arguments = JsonSerializer.Deserialize<Dictionary<string, object>>(toolCall.Arguments)!;
                        foreach (var argumentKvp in arguments)
                        {
                            functionArguments[argumentKvp.Key] = argumentKvp.Value.ToString();
                        }
                    }

                    var content = new FunctionCallContent(nameParts.Name, nameParts.PluginName, toolCall.Id, functionArguments);

                    functionSteps.Add(toolCall.Id, content);

                    yield return content;
                }
            }
        }

        async Task<ThreadMessage?> RetrieveMessageAsync(RunStepMessageCreationDetails detail, CancellationToken cancellationToken)
        {
            ThreadMessage? message = null;

            bool retry = false;
            int count = 0;
            do
            {
                try
                {
                    message = await client.GetMessageAsync(threadId, detail.MessageCreation.MessageId, cancellationToken).ConfigureAwait(false);
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

    private static ChatMessageContent GenerateMessageContent(string? assistantName, ThreadMessage message)
    {
        AuthorRole role = new(message.Role.ToString());

        ChatMessageContent content =
            new(role, content: null)
            {
                AuthorName = assistantName,
            };

        foreach (MessageContent itemContent in message.ContentItems)
        {
            // Process text content
            if (itemContent is MessageTextContent contentMessage)
            {
                content.Items.Add(new TextContent(contentMessage.Text.Trim()));

                foreach (MessageTextAnnotation annotation in contentMessage.Annotations)
                {
                    content.Items.Add(GenerateAnnotationContent(annotation));
                }
            }
            // Process image content
            else if (itemContent is MessageImageFileContent contentImage)
            {
                content.Items.Add(new FileReferenceContent(contentImage.FileId));
            }
        }

        return content;
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

    private static ChatMessageContent GenerateCodeInterpreterContent(string agentName, RunStepCodeInterpreterToolCall contentCodeInterpreter)
    {
        return
            new ChatMessageContent(
                AuthorRole.Assistant,
                [
                    new TextContent(contentCodeInterpreter.Input)
                ])
            {
                AuthorName = agentName,
                Metadata = new Dictionary<string, object?> { { OpenAIAssistantAgent.CodeInterpreterMetadataKey, true } },
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

            object resultValue = functionResult.Result ?? string.Empty;

            if (resultValue is not string textResult)
            {
                textResult = JsonSerializer.Serialize(resultValue);
            }

            toolOutputs[index] = new ToolOutput(functionResult.CallId, textResult!);
        }

        return toolOutputs;
    }
}
