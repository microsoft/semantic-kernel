// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.OpenAI.Internal;
using OpenAI.Assistants;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// A <see cref="AgentChannel"/> specialization for use with <see cref="OpenAIAssistantAgent"/>.
/// </summary>
internal sealed class OpenAIAssistantChannel(AssistantClient client, string threadId)
    : AgentChannel<OpenAIAssistantAgent>
{
    private readonly AssistantClient _client = client;
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

    private readonly AssistantsClient _client = client;
    private readonly string _threadId = threadId;

    /// <inheritdoc/>
    protected override async Task ReceiveAsync(IEnumerable<ChatMessageContent> history, CancellationToken cancellationToken)
    {
        foreach (ChatMessageContent message in history)
        {
            await AssistantThreadActions.CreateMessageAsync(this._client, this._threadId, message, cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc/>
    protected override IAsyncEnumerable<(bool IsVisible, ChatMessageContent Message)> InvokeAsync(
        OpenAIAssistantAgent agent,
        CancellationToken cancellationToken)
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
        int initialCapacity = 100; // Adjust this value based on the approximate number of steps
        HashSet<string> processedStepIds = new HashSet<string>(initialCapacity);
        Dictionary<string, FunctionCallContent> functionSteps = [];
        HashSet<string> processedStepIds = new HashSet<string>();
        Dictionary<string, FunctionCallContent> functionSteps = new Dictionary<string, FunctionCallContent>();

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
                FunctionCallContent[] activeFunctionSteps = steps.Data.SelectMany(step => ParseFunctionStep(agent, step)).ToArray();
                if (activeFunctionSteps.Length > 0)
                {
                    // Emit function-call content
{
    var functionCallContent = GenerateFunctionCallContent(agent.GetName(), activeFunctionSteps);
    await foreach (var content in functionCallContent)
    {
        yield return content;
    }
}

                    // Invoke functions for each tool-step
                    IEnumerable<Task<FunctionResultContent>> functionResultTasks = ExecuteFunctionSteps(agent, activeFunctionSteps, cancellationToken);

                    yield return GenerateFunctionCallContent(agent.GetName(), activeFunctionSteps);

                    // Block for function results
                    FunctionResultContent[] functionResults = await Task.WhenAll(functionResultTasks).ConfigureAwait(false);





                    // Invoke functions for each tool-step
                    IEnumerable<Task<FunctionResultContent>> functionResultTasks = ExecuteFunctionSteps(agent, activeFunctionSteps, cancellationToken);

                    // Block for function results
                    FunctionResultContent[] functionResults = await Task.WhenAll(functionResultTasks).ConfigureAwait(false);

                    // Process tool output
                    ToolOutput[] toolOutputs = GenerateToolOutputs(functionResults);

                    await this._client.SubmitToolOutputsToRunAsync(run, toolOutputs, cancellationToken).ConfigureAwait(false);
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
                            FunctionCallContent functionStep = functionSteps[toolFunction.Id]; // Function step always captured on invocation
                            content = GenerateFunctionResultContent(agent.GetName(), functionStep, toolFunction.Output);
                        }
        agent.ThrowIfDeleted();

        return AssistantThreadActions.InvokeAsync(agent, this._client, this._threadId, invocationOptions: null, this.Logger, agent.Kernel, agent.Arguments, cancellationToken);
    }

    /// <inheritdoc/>
    protected override IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(OpenAIAssistantAgent agent, IList<ChatMessageContent> messages, CancellationToken cancellationToken = default)
    {
        return AssistantThreadActions.InvokeStreamingAsync(agent, this._client, this._threadId, messages, invocationOptions: null, this.Logger, agent.Kernel, agent.Arguments, cancellationToken);

        agent.ThrowIfDeleted();

        return AssistantThreadActions.InvokeStreamingAsync(agent, this._client, this._threadId, messages, invocationOptions: null, this.Logger, agent.Kernel, agent.Arguments, cancellationToken);
        return AssistantThreadActions.InvokeAsync(agent, this._client, this._threadId, invocationOptions: null, this.Logger, agent.Kernel, agent.Arguments, cancellationToken);
    }

    /// <inheritdoc/>
    protected override IAsyncEnumerable<ChatMessageContent> GetHistoryAsync(CancellationToken cancellationToken)
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

        private IEnumerable<FunctionCallContent> ParseFunctionStep(OpenAIAssistantAgent agent, RunStep step)
        {
            // Implementation here
        }

        return await this._client.GetRunStepsAsync(run, cancellationToken: cancellationToken).ConfigureAwait(false);
        // Local function to capture kernel function state for further processing (participates in method closure).
        IEnumerable<FunctionCallContent> ParseFunctionStep(OpenAIAssistantAgent agent, RunStep step)
        {
            if (step.Status == RunStepStatus.InProgress && step.StepDetails is RunStepToolCallDetails callDetails)
            {
                foreach (RunStepFunctionToolCall toolCall in callDetails.ToolCalls.OfType<RunStepFunctionToolCall>())
                {
                    var nameParts = FunctionName.Parse(toolCall.Name, FunctionDelimiter.ToString());

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
            functionTasks[index] = ExecuteFunctionStepAsync(functionSteps[index]);
        }

        return functionTasks;
        }

        return functionTasks;
        }

        return functionTasks;

        async Task<FunctionResultContent> ExecuteFunctionStepAsync(FunctionCallContent functionStep)
        {
            FunctionResultContent functionResult = await functionStep.InvokeAsync(agent.Kernel, cancellationToken).ConfigureAwait(false);

            return functionResult;
        }
    }

    private static ToolOutput[] GenerateToolOutputs(FunctionResultContent[] functionResults)
    {
        ToolOutput[] toolOutputs = new ToolOutput[functionResults.Length];

        for (int index = 0; index < functionResults.Length; ++index)
        {
            FunctionResultContent functionResult = functionResults[index];

            object resultValue = functionResult.Result ?? string.Empty;

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

    private static ToolOutput[] GenerateToolOutputs(FunctionResultContent[] functionResults)
    {
        ToolOutput[] toolOutputs = new ToolOutput[functionResults.Length];

        for (int index = 0; index < functionResults.Length; ++index)
        {
            FunctionResultContent functionResult = functionResults[index];

            object resultValue = functionResult.Result ?? string.Empty;


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

    private async Task<ThreadMessage?> RetrieveMessageAsync(RunStepMessageCreationDetails detail, CancellationToken cancellationToken)
    {
        return AssistantThreadActions.GetMessagesAsync(this._client, this._threadId, cancellationToken);
    }

    /// <inheritdoc/>
    protected override Task ResetAsync(CancellationToken cancellationToken = default) =>
        this._client.DeleteThreadAsync(this._threadId, cancellationToken);

    protected override string Serialize() => this._threadId;
}
