// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Azure;
using Azure.AI.Agents.Persistent;
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
           this PersistentAgentsClient client,
           ThreadRun run,
           [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        AsyncPageable<RunStep>? steps = client.Runs.GetRunStepsAsync(run, cancellationToken: cancellationToken);
        await foreach (RunStep step in steps.ConfigureAwait(false))
        {
            yield return step;
        }
    }

    public static async Task<ThreadRun> CreateAsync(
        this PersistentAgentsClient client,
        string threadId,
        AzureAIAgent agent,
        string? instructions,
        ToolDefinition[] tools,
        AzureAIInvocationOptions? invocationOptions,
        CancellationToken cancellationToken)
    {
        Truncation? truncationStrategy = GetTruncationStrategy(invocationOptions);
        BinaryData? responseFormat = GetResponseFormat(invocationOptions);
        return
            await client.Runs.CreateRunAsync(
                threadId,
                agent.Id,
                overrideModelName: invocationOptions?.ModelName,
                overrideInstructions: invocationOptions?.OverrideInstructions ?? instructions,
                additionalInstructions: invocationOptions?.AdditionalInstructions,
                additionalMessages: [.. AgentMessageFactory.GetThreadMessages(invocationOptions?.AdditionalMessages)],
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
            BinaryData.FromString(
                """
                {
                    "type": "json_object"
                }                        
                """) :
            null;
    }

    private static Truncation? GetTruncationStrategy(AzureAIInvocationOptions? invocationOptions)
    {
        return invocationOptions?.TruncationMessageCount == null ?
            null :
            new(TruncationStrategy.LastMessages)
            {
                LastMessages = invocationOptions.TruncationMessageCount
            };
    }

    public static IAsyncEnumerable<StreamingUpdate> CreateStreamingAsync(
        this PersistentAgentsClient client,
        string threadId,
        AzureAIAgent agent,
        string? instructions,
        ToolDefinition[] tools,
        AzureAIInvocationOptions? invocationOptions,
        CancellationToken cancellationToken)
    {
        Truncation? truncationStrategy = GetTruncationStrategy(invocationOptions);
        BinaryData? responseFormat = GetResponseFormat(invocationOptions);
        return
            client.Runs.CreateRunStreamingAsync(
                threadId,
                agent.Id,
                overrideModelName: invocationOptions?.ModelName,
                overrideInstructions: invocationOptions?.OverrideInstructions ?? instructions,
                additionalInstructions: invocationOptions?.AdditionalInstructions,
                additionalMessages: [.. AgentMessageFactory.GetThreadMessages(invocationOptions?.AdditionalMessages)],
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
