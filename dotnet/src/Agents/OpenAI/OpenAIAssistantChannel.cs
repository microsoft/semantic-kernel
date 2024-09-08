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
                    yield return GenerateFunctionCallContent(agent.GetName(), activeFunctionSteps);

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
    protected override IAsyncEnumerable<ChatMessageContent> GetHistoryAsync(CancellationToken cancellationToken)
    {
        return AssistantThreadActions.GetMessagesAsync(this._client, this._threadId, cancellationToken);
    }

    /// <inheritdoc/>
    protected override Task ResetAsync(CancellationToken cancellationToken = default) =>
        this._client.DeleteThreadAsync(this._threadId, cancellationToken);
}
