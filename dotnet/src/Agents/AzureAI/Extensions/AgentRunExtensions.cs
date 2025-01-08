// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using Microsoft.SemanticKernel.Agents.AzureAI.Internal;
using System.Threading.Tasks;
using AzureAIP = Azure.AI.Projects;
using System.Linq;

namespace Microsoft.SemanticKernel.Agents.AzureAI.Extensions;

/// <summary>
/// %%%
/// </summary>
/// <remarks>
/// Improves testability.
/// </remarks>
internal static class AgentRunExtensions
{
    public static async IAsyncEnumerable<AzureAIP.RunStep> GetStepsAsync(
        this AzureAIP.AgentsClient client,
        AzureAIP.ThreadRun run,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        AzureAIP.PageableList<AzureAIP.RunStep>? steps = null;
        do
        {
            steps = await client.GetRunStepsAsync(run, cancellationToken: cancellationToken).ConfigureAwait(false);
            foreach (AzureAIP.RunStep step in steps)
            {
                yield return step;
            }
        }
        while (steps?.HasMore ?? false);
    }

    public static async Task<AzureAIP.ThreadRun> CreateAsync(
        this AzureAIP.AgentsClient client,
        string threadId,
        AzureAIAgent agent,
        string? instructions,
        AzureAIP.ToolDefinition[] tools,
        bool isStreaming,
        AzureAIInvocationOptions? invocationOptions,
        CancellationToken cancellationToken)
    {
        return
            await client.CreateRunAsync(
                threadId,
                agent.Definition.Id,
                overrideModelName: invocationOptions?.ModelName,
                instructions,
                additionalInstructions: invocationOptions?.AdditionalInstructions,
                additionalMessages: AgentMessageFactory.GetThreadMessages(invocationOptions?.AdditionalMessages).ToArray(),
                overrideTools: tools,
                stream: isStreaming,
                temperature: invocationOptions?.Temperature,
                topP: invocationOptions?.TopP,
                maxPromptTokens: invocationOptions?.MaxPromptTokens,
                maxCompletionTokens: invocationOptions?.MaxCompletionTokens,
                truncationStrategy: null, // %%%
                toolChoice: null, // %%%
                responseFormat: null, // %%%
                parallelToolCalls: invocationOptions?.ParallelToolCallsEnabled,
                metadata: invocationOptions?.Metadata,
                cancellationToken).ConfigureAwait(false);
    }
}
