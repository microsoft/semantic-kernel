// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.Projects;
using Microsoft.SemanticKernel.Agents.AzureAI.Internal;

namespace Microsoft.SemanticKernel.Agents.AzureAI.Extensions;

/// <summary>
/// Extensions associated with an Agent run processing.
/// </summary>
/// <remarks>
/// Improves testability.
/// </remarks>
internal static class AgentRunExtensions
{
    public static async IAsyncEnumerable<RunStep> GetStepsAsync(
        this AgentsClient client,
        ThreadRun run,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        PageableList<RunStep>? steps = null;
        do
        {
            steps = await client.GetRunStepsAsync(run, after: steps?.LastId, cancellationToken: cancellationToken).ConfigureAwait(false);
            foreach (RunStep step in steps)
            {
                yield return step;
            }
        }
        while (steps?.HasMore ?? false);
    }

    public static async Task<ThreadRun> CreateAsync(
        this AgentsClient client,
        string threadId,
        AzureAIAgent agent,
        string? instructions,
        ToolDefinition[] tools,
        AzureAIInvocationOptions? invocationOptions,
        CancellationToken cancellationToken)
    {
        TruncationObject? truncationStrategy = GetTruncationStrategy(invocationOptions);
        BinaryData? responseFormat = GetResponseFormat(invocationOptions);
        return
            await client.CreateRunAsync(
                threadId,
                agent.Definition.Id,
                overrideModelName: invocationOptions?.ModelName,
                overrideInstructions: invocationOptions?.OverrideInstructions ?? instructions,
                additionalInstructions: invocationOptions?.AdditionalInstructions,
                additionalMessages: AgentMessageFactory.GetThreadMessages(invocationOptions?.AdditionalMessages).ToArray(),
                overrideTools: tools,
                stream: false,
                temperature: invocationOptions?.Temperature,
                topP: invocationOptions?.TopP,
                maxPromptTokens: invocationOptions?.MaxPromptTokens,
                maxCompletionTokens: invocationOptions?.MaxCompletionTokens,
                truncationStrategy,
                toolChoice: null,
                responseFormat,
                parallelToolCalls: invocationOptions?.ParallelToolCallsEnabled,
                metadata: invocationOptions?.Metadata,
                include: null,
                cancellationToken).ConfigureAwait(false);
    }

    private static BinaryData? GetResponseFormat(AzureAIInvocationOptions? invocationOptions)
    {
        return invocationOptions?.EnableJsonResponse == true ?
            BinaryData.FromString(ResponseFormat.JsonObject.ToString()) :
            null;
    }

    private static TruncationObject? GetTruncationStrategy(AzureAIInvocationOptions? invocationOptions)
    {
        return invocationOptions?.TruncationMessageCount == null ?
            null :
            new(TruncationStrategy.LastMessages)
            {
                LastMessages = invocationOptions.TruncationMessageCount
            };
    }

    public static IAsyncEnumerable<StreamingUpdate> CreateStreamingAsync(
        this AgentsClient client,
        string threadId,
        AzureAIAgent agent,
        string? instructions,
        ToolDefinition[] tools,
        AzureAIInvocationOptions? invocationOptions,
        CancellationToken cancellationToken)
    {
        TruncationObject? truncationStrategy = GetTruncationStrategy(invocationOptions);
        BinaryData? responseFormat = GetResponseFormat(invocationOptions);
        return
            client.CreateRunStreamingAsync(
                threadId,
                agent.Definition.Id,
                overrideModelName: invocationOptions?.ModelName,
                overrideInstructions: invocationOptions?.OverrideInstructions ?? instructions,
                additionalInstructions: invocationOptions?.AdditionalInstructions,
                additionalMessages: AgentMessageFactory.GetThreadMessages(invocationOptions?.AdditionalMessages).ToArray(),
                overrideTools: tools,
                temperature: invocationOptions?.Temperature,
                topP: invocationOptions?.TopP,
                maxPromptTokens: invocationOptions?.MaxPromptTokens,
                maxCompletionTokens: invocationOptions?.MaxCompletionTokens,
                truncationStrategy,
                toolChoice: null,
                responseFormat,
                parallelToolCalls: invocationOptions?.ParallelToolCallsEnabled,
                metadata: invocationOptions?.Metadata,
                cancellationToken);
    }
}
