// Copyright (c) Microsoft. All rights reserved.
using System;
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
using System.ClientModel;
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
using System.ClientModel;
=======
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
using System.ClientModel;
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
using System.ClientModel;
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
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
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
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
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
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
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======


                ThreadInitializationMessage threadMessage = new(AssistantMessageFactory.GetMessageContents(message));
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======


                ThreadInitializationMessage threadMessage = new(AssistantMessageFactory.GetMessageContents(message));
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
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

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        await foreach (PageResult<ThreadMessage> page in client.GetMessagesAsync(threadId, new() { Order = ListOrder.NewestFirst }, cancellationToken).ConfigureAwait(false))
        {
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
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        await foreach (ThreadMessage message in client.GetMessagesAsync(threadId, new() { Order = MessageCollectionOrder.Descending }, cancellationToken).ConfigureAwait(false))
        {
            foreach (ThreadMessage message in page.Values)
            foreach (var message in page.Values)
        await foreach (ThreadMessage message in client.GetMessagesAsync(threadId, ListOrder.NewestFirst, cancellationToken).ConfigureAwait(false))
        {
            AuthorRole role = new(message.Role.ToString());

            string? assistantName = null;
            if (!string.IsNullOrWhiteSpace(message.AssistantId) &&
                !agentNames.TryGetValue(message.AssistantId, out assistantName))
            {
                Assistant assistant = await client.GetAssistantAsync(message.AssistantId, cancellationToken).ConfigureAwait(false);
                Assistant assistant = await client.GetAssistantAsync(message.AssistantId).ConfigureAwait(false); // SDK BUG - CANCEL TOKEN (https://github.com/microsoft/semantic-kernel/issues/7431)
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
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
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

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
        string? instructions = await agent.GetInstructionsAsync(kernel, arguments, cancellationToken).ConfigureAwait(false);

        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(agent.Definition, instructions, invocationOptions);
        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(agent.Definition, invocationOptions);
        string? instructions = await agent.GetInstructionsAsync(kernel, arguments, cancellationToken).ConfigureAwait(false);

        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(agent.Definition, instructions, invocationOptions);
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(agent.Definition, invocationOptions);

        options.ToolsOverride.AddRange(tools);

        ThreadRun run = await client.CreateRunAsync(threadId, agent.Id, options, cancellationToken).ConfigureAwait(false);

        logger.LogOpenAIAssistantCreatedRun(nameof(InvokeAsync), run.Id, threadId);

        // Evaluate status and process steps and messages, as encountered.
        HashSet<string> processedStepIds = [];
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        Dictionary<string, FunctionResultContent> functionSteps = [];
        Dictionary<string, FunctionCallContent> functionSteps = [];
        Dictionary<string, FunctionResultContent> functionSteps = [];
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        Dictionary<string, FunctionResultContent> functionSteps = [];
        Dictionary<string, FunctionCallContent> functionSteps = [];
        Dictionary<string, FunctionResultContent> functionSteps = [];
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
        Dictionary<string, FunctionResultContent> functionSteps = [];
        Dictionary<string, FunctionCallContent> functionSteps = [];
        Dictionary<string, FunctionResultContent> functionSteps = [];
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
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

            IReadOnlyList<RunStep> steps = await GetRunStepsAsync(client, run).ConfigureAwait(false);
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
            List<RunStep> steps = [];
            await foreach (var page in client.GetRunStepsAsync(run).ConfigureAwait(false))
            {
                steps.AddRange(page.Values);
            };
            IReadOnlyList<RunStep> steps = await GetRunStepsAsync(client, run, cancellationToken).ConfigureAwait(false);
            RunStep[] steps = await client.GetRunStepsAsync(run).ToArrayAsync(cancellationToken).ConfigureAwait(false);
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head

            // Is tool action required?
            if (run.Status == RunStatus.RequiresAction)
            {
                logger.LogOpenAIAssistantProcessingRunSteps(nameof(InvokeAsync), run.Id, threadId);

                // Execute functions in parallel and post results at once.
                FunctionCallContent[] functionCalls = steps.SelectMany(step => ParseFunctionStep(agent, step)).ToArray();
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
                // Capture function-call for message processing
                foreach (FunctionCallContent functionCall in functionCalls)
                {
                    functionSteps.Add(functionCall.Id!, functionCall);
                }
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
                if (functionCalls.Length > 0)
                {
                    // Emit function-call content
                    yield return (IsVisible: false, Message: GenerateFunctionCallContent(agent.GetName(), functionCalls));

                    // Invoke functions for each tool-step
                    IEnumerable<Task<FunctionResultContent>> functionResultTasks = ExecuteFunctionSteps(agent, functionCalls, cancellationToken);
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
                FunctionCallContent[] activeFunctionSteps = steps.SelectMany(step => ParseFunctionStep(agent, step)).ToArray();
                if (activeFunctionSteps.Length > 0)
                {
                    // Emit function-call content
                    yield return (IsVisible: false, Message: GenerateFunctionCallContent(agent.GetName(), activeFunctionSteps));

                    // Invoke functions for each tool-step
                    IEnumerable<Task<FunctionResultContent>> functionResultTasks = ExecuteFunctionSteps(agent, activeFunctionSteps, cancellationToken);
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head

                    // Block for function results
                    FunctionResultContent[] functionResults = await Task.WhenAll(functionResultTasks).ConfigureAwait(false);

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
                    // Capture function-call for message processing
                    foreach (FunctionResultContent functionCall in functionResults) // %%%
                    // Capture function-call for message processing
                    foreach (FunctionResultContent functionCall in functionResults)
                    {
                        functionSteps.Add(functionCall.CallId!, functionCall);
                    }

<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
                    // Process tool output
                    ToolOutput[] toolOutputs = GenerateToolOutputs(functionResults);

                    await client.SubmitToolOutputsToRunAsync(threadId, run.Id, toolOutputs, cancellationToken).ConfigureAwait(false);
                }

                logger.LogOpenAIAssistantProcessedRunSteps(nameof(InvokeAsync), functionCalls.Length, run.Id, threadId);
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
                logger.LogOpenAIAssistantProcessedRunSteps(nameof(InvokeAsync), activeFunctionSteps.Length, run.Id, threadId);
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
                logger.LogOpenAIAssistantProcessedRunSteps(nameof(InvokeAsync), activeFunctionSteps.Length, run.Id, threadId);
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
                logger.LogOpenAIAssistantProcessedRunSteps(nameof(InvokeAsync), activeFunctionSteps.Length, run.Id, threadId);
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
                logger.LogOpenAIAssistantProcessedRunSteps(nameof(InvokeAsync), activeFunctionSteps.Length, run.Id, threadId);
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
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
                            content = GenerateCodeInterpreterContent(agent.GetName(), toolCall.CodeInterpreterInput, completedStep);
                            isVisible = true;
                        }
                        // Process function result content
                        else if (toolCall.ToolKind == RunStepToolCallKind.Function)
                        {
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
                            FunctionResultContent functionStep = functionSteps[toolCall.ToolCallId]; // Function step always captured on invocation
                            content = GenerateFunctionResultContent(agent.GetName(), [functionStep]);
                            FunctionCallContent functionStep = functionSteps[toolCall.ToolCallId]; // Function step always captured on invocation
                            content = GenerateFunctionResultContent(agent.GetName(), functionStep, toolCall.FunctionOutput);
                            FunctionResultContent functionStep = functionSteps[toolCall.ToolCallId]; // Function step always captured on invocation
<<<<<<< main
                            content = GenerateFunctionResultContent(agent.GetName(), [functionStep]);
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
                            FunctionCallContent functionStep = functionSteps[toolCall.ToolCallId]; // Function step always captured on invocation
                            content = GenerateFunctionResultContent(agent.GetName(), functionStep, toolCall.FunctionOutput);
=======
                            content = GenerateFunctionResultContent(agent.GetName(), [functionStep], completedStep);
>>>>>>> upstream/main
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
                    ThreadMessage? message = await RetrieveMessageAsync(client, threadId, completedStep.Details.CreatedMessageId, agent.PollingOptions.MessageSynchronizationDelay, cancellationToken).ConfigureAwait(false);
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

                    if (message is not null)
                    {
=======
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes

                    if (message is not null)
                    {
=======
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
                    ThreadMessage? message = await RetrieveMessageAsync(completedStep.Details.CreatedMessageId, cancellationToken).ConfigureAwait(false);

                    if (message is not null)
                    {
                        ChatMessageContent content = GenerateMessageContent(agent.GetName(), message, completedStep);
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
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
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        IList<ChatMessageContent> messages,
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        IList<ChatMessageContent> messages,
=======
        IList<ChatMessageContent>? messages,
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        IList<ChatMessageContent>? messages,
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
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

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(agent.Definition, invocationOptions);
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(agent.Definition, invocationOptions);
=======
        string? instructions = await agent.GetInstructionsAsync(kernel, arguments, cancellationToken).ConfigureAwait(false);

        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(agent.Definition, instructions, invocationOptions);
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        string? instructions = await agent.GetInstructionsAsync(kernel, arguments, cancellationToken).ConfigureAwait(false);

        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(agent.Definition, instructions, invocationOptions);
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head

        options.ToolsOverride.AddRange(tools);

        // Evaluate status and process steps and messages, as encountered.
        HashSet<string> processedStepIds = [];
<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        HashSet<string> messageIds = [];

        ThreadRun? run = null;
        IAsyncEnumerable<StreamingUpdate> asyncUpdates = client.CreateRunStreamingAsync(threadId, agent.Id, options, cancellationToken);
        do
        {
            messageIds.Clear();
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
=======
<<<<<<< div
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        Dictionary<string, RunStep?> activeMessages = [];
=======
        Dictionary<string, FunctionResultContent[]> stepFunctionResults = [];
        List<RunStep> stepsToProcess = [];
>>>>>>> upstream/main
        ThreadRun? run = null;

        IAsyncEnumerable<StreamingUpdate> asyncUpdates = client.CreateRunStreamingAsync(threadId, agent.Id, options, cancellationToken);
        do
        {
<<<<<<< main
            activeMessages.Clear();
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
            stepsToProcess.Clear();
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div

            await foreach (StreamingUpdate update in asyncUpdates.ConfigureAwait(false))
            {
                if (update is RunUpdate runUpdate)
                {
                    run = runUpdate.Value;

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
                    logger.LogOpenAIAssistantCreatedRun(nameof(InvokeAsync), run.Id, threadId);
                }
                else if (update is MessageContentUpdate contentUpdate)
                {
                    messageIds.Add(contentUpdate.MessageId);
                    yield return GenerateStreamingMessageContent(agent.GetName(), contentUpdate);
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
                    switch (runUpdate.UpdateKind)
                    {
                        case StreamingUpdateReason.RunCreated:
                            logger.LogOpenAIAssistantCreatedRun(nameof(InvokeAsync), run.Id, threadId);
                            break;
                    }
                }
                else if (update is MessageContentUpdate contentUpdate)
                {
                    switch (contentUpdate.UpdateKind)
                    {
                        case StreamingUpdateReason.MessageUpdated:
                            yield return GenerateStreamingMessageContent(agent.GetName(), contentUpdate);
                            break;
                    }
                }
                else if (update is RunStepDetailsUpdate detailsUpdate)
                {
                    StreamingChatMessageContent? toolContent = GenerateStreamingCodeInterpreterContent(agent.GetName(), detailsUpdate);
                    if (toolContent != null)
                    {
                        yield return toolContent;
                    }
                }
                else if (update is RunStepUpdate stepUpdate)
                {
                    switch (stepUpdate.UpdateKind)
                    {
                        case StreamingUpdateReason.RunStepCompleted:
                            stepsToProcess.Add(stepUpdate.Value);
                            break;
                        default:
                            break;
                    }
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
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
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
                IReadOnlyList<RunStep> steps = await GetRunStepsAsync(client, run).ConfigureAwait(false);
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
                IReadOnlyList<RunStep> steps = await GetRunStepsAsync(client, run).ConfigureAwait(false);
=======
                IReadOnlyList<RunStep> steps = await GetRunStepsAsync(client, run, cancellationToken).ConfigureAwait(false);
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
                IReadOnlyList<RunStep> steps = await GetRunStepsAsync(client, run, cancellationToken).ConfigureAwait(false);
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head

                // Capture map between the tool call and its associated step
                Dictionary<string, string> toolMap = [];
                foreach (RunStep step in steps)
                {
                    foreach (RunStepToolCall stepDetails in step.Details.ToolCalls)
                    {
                        toolMap[stepDetails.ToolCallId] = step.Id;
                    }
                }

                // Execute functions in parallel and post results at once.
                FunctionCallContent[] functionCalls = steps.SelectMany(step => ParseFunctionStep(agent, step)).ToArray();
                if (functionCalls.Length > 0)
                {
                    // Emit function-call content
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
                    messages.Add(GenerateFunctionCallContent(agent.GetName(), functionCalls));
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
                    messages.Add(GenerateFunctionCallContent(agent.GetName(), functionCalls));
=======
                    messages?.Add(GenerateFunctionCallContent(agent.GetName(), functionCalls));
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
                    messages?.Add(GenerateFunctionCallContent(agent.GetName(), functionCalls));
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head

                    // Invoke functions for each tool-step
                    IEnumerable<Task<FunctionResultContent>> functionResultTasks = ExecuteFunctionSteps(agent, functionCalls, cancellationToken);

                    // Block for function results
                    FunctionResultContent[] functionResults = await Task.WhenAll(functionResultTasks).ConfigureAwait(false);

                    // Process tool output
                    ToolOutput[] toolOutputs = GenerateToolOutputs(functionResults);
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
                    asyncUpdates = client.SubmitToolOutputsToRunStreamingAsync(run, toolOutputs);

                    messages.Add(GenerateFunctionResultsContent(agent.GetName(), functionResults));
                }
            }

            if (messageIds.Count > 0)
            {
                logger.LogOpenAIAssistantProcessingRunMessages(nameof(InvokeAsync), run!.Id, threadId);

                foreach (string messageId in messageIds)
                {
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
=======
<<<<<<< div
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
>>>>>>> head
                    asyncUpdates = client.SubmitToolOutputsToRunStreamingAsync(run.ThreadId, run.Id, toolOutputs, cancellationToken);

<<<<<<< main
                    messages.Add(GenerateFunctionResultContent(agent.GetName(), functionResults));
                    messages?.Add(GenerateFunctionResultContent(agent.GetName(), functionResults));
=======
                    foreach (RunStep step in steps)
                    {
                        stepFunctionResults.Add(step.Id, functionResults.Where(result => step.Id == toolMap[result.CallId!]).ToArray());
                    }
>>>>>>> upstream/main
                }
            }

            if (stepsToProcess.Count > 0)
            {
                logger.LogOpenAIAssistantProcessingRunMessages(nameof(InvokeAsync), run!.Id, threadId);

                foreach (RunStep step in stepsToProcess)
                {
<<<<<<< main
                    RunStep? step = activeMessages[messageId];
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
                    ThreadMessage? message = await RetrieveMessageAsync(client, threadId, messageId, agent.PollingOptions.MessageSynchronizationDelay, cancellationToken).ConfigureAwait(false);

                    if (message != null)
                    {
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
                        ChatMessageContent content = GenerateMessageContent(agent.GetName(), message);
                        messages.Add(content);
                    }
                }

                logger.LogOpenAIAssistantProcessedRunMessages(nameof(InvokeAsync), messageIds.Count, run!.Id, threadId);
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
<<<<<<< div
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
>>>>>>> head
                        ChatMessageContent content = GenerateMessageContent(agent.GetName(), message, step);
                        messages?.Add(content);
                    }
                }

                logger.LogOpenAIAssistantProcessedRunMessages(nameof(InvokeAsync), activeMessages.Count, run!.Id, threadId);
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
                    if (!string.IsNullOrEmpty(step.Details.CreatedMessageId))
                    {
                        ThreadMessage? message =
                            await RetrieveMessageAsync(
                                client,
                                threadId,
                                step.Details.CreatedMessageId,
                                agent.PollingOptions.MessageSynchronizationDelay,
                                cancellationToken).ConfigureAwait(false);

                        if (message != null)
                        {
                            ChatMessageContent content = GenerateMessageContent(agent.GetName(), message, step);
                            messages?.Add(content);
                        }
                    }
                    else
                    {
                        foreach (RunStepToolCall toolCall in step.Details.ToolCalls)
                        {
                            switch (toolCall.ToolKind)
                            {
                                case RunStepToolCallKind.CodeInterpreter:
                                    messages?.Add(GenerateCodeInterpreterContent(agent.GetName(), toolCall.CodeInterpreterInput, step));
                                    break;
                                case RunStepToolCallKind.Function:
                                    messages?.Add(GenerateFunctionResultContent(agent.GetName(), stepFunctionResults[step.Id], step));
                                    stepFunctionResults.Remove(step.Id);
                                    break;
                            }
                        }
                    }
                }

                logger.LogOpenAIAssistantProcessedRunMessages(nameof(InvokeAsync), stepsToProcess.Count, run!.Id, threadId);
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
            }
        }
        while (run?.Status != RunStatus.Completed);

        logger.LogOpenAIAssistantCompletedRun(nameof(InvokeAsync), run?.Id ?? "Failed", threadId);
    }

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    private static async Task<IReadOnlyList<RunStep>> GetRunStepsAsync(AssistantClient client, ThreadRun run)
    {
        List<RunStep> steps = [];

        await foreach (PageResult<RunStep> page in client.GetRunStepsAsync(run).ConfigureAwait(false))
        {
            steps.AddRange(page.Values);
        };

        return steps;
    }

<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
=======
<<<<<<< div
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    private static async Task<IReadOnlyList<RunStep>> GetRunStepsAsync(AssistantClient client, ThreadRun run, CancellationToken cancellationToken)
    {
        List<RunStep> steps = [];

        await foreach (RunStep step in client.GetRunStepsAsync(run.ThreadId, run.Id, cancellationToken: cancellationToken).ConfigureAwait(false))
        {
            steps.Add(step);
        }

        return steps;

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

    private static ChatMessageContent GenerateMessageContent(string? assistantName, ThreadMessage message, RunStep? completedStep = null)
    {
        AuthorRole role = new(message.Role.ToString());

        Dictionary<string, object?>? metadata =
            new()
            {
                { nameof(ThreadMessage.CreatedAt), message.CreatedAt },
                { nameof(ThreadMessage.AssistantId), message.AssistantId },
                { nameof(ThreadMessage.ThreadId), message.ThreadId },
                { nameof(ThreadMessage.RunId), message.RunId },
                { nameof(MessageContentUpdate.MessageId), message.Id },
            };

        if (completedStep != null)
        {
            metadata[nameof(RunStepDetailsUpdate.StepId)] = completedStep.Id;
            metadata[nameof(RunStep.Usage)] = completedStep.Usage;
        }

<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    private static ChatMessageContent GenerateMessageContent(string? assistantName, ThreadMessage message)
    {
        AuthorRole role = new(message.Role.ToString());

        ChatMessageContent content =
            new(role, content: null)
            {
                AuthorName = assistantName,
<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
                Metadata = metaData,
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
                Metadata = metaData,
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
                Metadata = metaData,
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
                Metadata = metaData,
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
                Metadata = metadata,
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
            };

        foreach (MessageContent itemContent in message.Content)
        {
            // Process text content
            if (!string.IsNullOrEmpty(itemContent.Text))
            {
                content.Items.Add(new TextContent(itemContent.Text));
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
                content.Items.Add(new TextContent(itemContent.Text.Trim()));
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
                content.Items.Add(new TextContent(itemContent.Text.Trim()));
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
                content.Items.Add(new TextContent(itemContent.Text.Trim()));
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
                content.Items.Add(new TextContent(itemContent.Text.Trim()));
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head

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

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
    private static StreamingChatMessageContent? GenerateStreamingCodeInterpreterContent(string? assistantName, RunStepDetailsUpdate update)
    {
        StreamingChatMessageContent content =
            new(AuthorRole.Assistant, content: null)
            {
                AuthorName = assistantName,
            };

        // Process text content
        if (update.CodeInterpreterInput != null)
        {
            content.Items.Add(new StreamingTextContent(update.CodeInterpreterInput));
            content.Metadata = new Dictionary<string, object?> { { OpenAIAssistantAgent.CodeInterpreterMetadataKey, true } };
        }

        if ((update.CodeInterpreterOutputs?.Count ?? 0) > 0)
        {
            foreach (var output in update.CodeInterpreterOutputs!)
            {
                if (output.ImageFileId != null)
                {
                    content.Items.Add(new StreamingFileReferenceContent(output.ImageFileId));
                }
            }
        }

        return content.Items.Count > 0 ? content : null;
    }

<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
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
            new(annotation.TextToReplace)
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
            new()
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
            new()
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
            new()
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
            new()
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
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

    private static ChatMessageContent GenerateCodeInterpreterContent(string agentName, string pythonCode, RunStep completedStep)
    {
        Dictionary<string, object?> metadata = GenerateToolCallMetadata(completedStep);
        metadata[OpenAIAssistantAgent.CodeInterpreterMetadataKey] = true;

        return
            new ChatMessageContent(
                AuthorRole.Assistant,
                [
                    new TextContent(pythonCode)
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
                    new TextContent(code)
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
                    new TextContent(code)
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
                    new TextContent(code)
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
                    new TextContent(code)
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
                ])
            {
                AuthorName = agentName,
                Metadata = metadata,
            };
    }

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
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
    private static ChatMessageContent GenerateFunctionCallContent(string agentName, FunctionCallContent[] functionSteps)
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
    private static ChatMessageContent GenerateFunctionCallContent(string agentName, FunctionCallContent[] functionSteps)
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
    private static ChatMessageContent GenerateFunctionCallContent(string agentName, FunctionCallContent[] functionSteps)
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
    private static ChatMessageContent GenerateFunctionCallContent(string agentName, FunctionCallContent[] functionSteps)
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    {
        ChatMessageContent functionCallContent = new(AuthorRole.Assistant, content: null)
        {
            AuthorName = agentName
        };

        functionCallContent.Items.AddRange(functionCalls);
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
        functionCallContent.Items.AddRange(functionSteps);
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        functionCallContent.Items.AddRange(functionSteps);
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
        functionCallContent.Items.AddRange(functionSteps);
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
        functionCallContent.Items.AddRange(functionSteps);
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head

        return functionCallContent;
    }

<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    private static ChatMessageContent GenerateFunctionResultContent(string agentName, FunctionCallContent functionCall, string result)
    {
        ChatMessageContent functionCallContent = new(AuthorRole.Tool, content: null)
        {
            AuthorName = agentName
        };

        functionCallContent.Items.Add(
            new FunctionResultContent(
                functionCall.FunctionName,
                functionCall.PluginName,
                functionCall.Id,
                result));

        return functionCallContent;
    }

    private static ChatMessageContent GenerateFunctionResultsContent(string agentName, IList<FunctionResultContent> functionResults)
=======
    private static ChatMessageContent GenerateFunctionResultContent(string agentName, FunctionResultContent[] functionResults, RunStep completedStep)
>>>>>>> upstream/main
    {
        ChatMessageContent functionResultContent = new(AuthorRole.Tool, content: null)
        {
            AuthorName = agentName,
            Metadata = GenerateToolCallMetadata(completedStep),
        };

<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
=======
<<<<<<< div
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    private static ChatMessageContent GenerateFunctionResultContent(string agentName, FunctionResultContent[] functionResults)
    {
        ChatMessageContent functionResultContent = new(AuthorRole.Tool, content: null)
    private static ChatMessageContent GenerateFunctionResultContent(string agentName, FunctionCallContent functionStep, string result)
    {
        ChatMessageContent functionCallContent = new(AuthorRole.Tool, content: null)
        {
            AuthorName = agentName
        };
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
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

    private static Dictionary<string, object?> GenerateToolCallMetadata(RunStep completedStep)
    {
        return new()
            {
                { nameof(RunStep.CreatedAt), completedStep.CreatedAt },
                { nameof(RunStep.AssistantId), completedStep.AssistantId },
                { nameof(RunStep.ThreadId), completedStep.ThreadId },
                { nameof(RunStep.RunId), completedStep.RunId },
                { nameof(RunStepDetailsUpdate.StepId), completedStep.Id },
                { nameof(RunStep.Usage), completedStep.Usage },
            };
    }

    private static Task<FunctionResultContent>[] ExecuteFunctionSteps(OpenAIAssistantAgent agent, FunctionCallContent[] functionCalls, CancellationToken cancellationToken)
    {
        Task<FunctionResultContent>[] functionTasks = new Task<FunctionResultContent>[functionCalls.Length];

        for (int index = 0; index < functionCalls.Length; ++index)
        {
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            functionTasks[index] = functionCalls[index].InvokeAsync(agent.Kernel, cancellationToken);
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
            functionTasks[index] = functionCalls[index].InvokeAsync(agent.Kernel, cancellationToken);
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
            functionTasks[index] = functionCalls[index].InvokeAsync(agent.Kernel, cancellationToken);
=======
>>>>>>> Stashed changes
=======
            functionTasks[index] = functionCalls[index].InvokeAsync(agent.Kernel, cancellationToken);
=======
>>>>>>> Stashed changes
>>>>>>> head
            functionTasks[index] = ExecuteFunctionStep(agent, functionCalls[index], cancellationToken);

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
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
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
