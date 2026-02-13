// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using Microsoft.SemanticKernel.Agents.Extensions;
using OpenAI.Responses;

namespace Microsoft.SemanticKernel.Agents.OpenAI.Internal;

/// <summary>
/// Factory for creating instances of <see cref="CreateResponseOptions"/>.
/// </summary>
internal static class ResponseCreationOptionsFactory
{
    internal static CreateResponseOptions CreateOptions(
        OpenAIResponseAgent agent,
        AgentThread agentThread,
        AgentInvokeOptions? invokeOptions)
    {
        var instructions = $"{agent.Instructions}{(string.IsNullOrEmpty(agent.Instructions) || string.IsNullOrEmpty(invokeOptions?.AdditionalInstructions) ? "" : "\n")}{invokeOptions?.AdditionalInstructions}";
        CreateResponseOptions creationOptions;
        if (invokeOptions is OpenAIResponseAgentInvokeOptions responseAgentInvokeOptions &&
            responseAgentInvokeOptions.ResponseCreationOptions is not null)
        {
            creationOptions = new CreateResponseOptions
            {
                EndUserId = responseAgentInvokeOptions.ResponseCreationOptions.EndUserId ?? agent.GetDisplayName(),
                Instructions = responseAgentInvokeOptions.ResponseCreationOptions.Instructions ?? instructions,
                StoredOutputEnabled = responseAgentInvokeOptions.ResponseCreationOptions.StoredOutputEnabled ?? agent.StoreEnabled,
                BackgroundModeEnabled = responseAgentInvokeOptions.ResponseCreationOptions.BackgroundModeEnabled,
                ReasoningOptions = responseAgentInvokeOptions.ResponseCreationOptions.ReasoningOptions,
                MaxOutputTokenCount = responseAgentInvokeOptions.ResponseCreationOptions.MaxOutputTokenCount,
                TextOptions = responseAgentInvokeOptions.ResponseCreationOptions.TextOptions,
                TruncationMode = responseAgentInvokeOptions.ResponseCreationOptions.TruncationMode,
                ParallelToolCallsEnabled = responseAgentInvokeOptions.ResponseCreationOptions.ParallelToolCallsEnabled,
                ToolChoice = responseAgentInvokeOptions.ResponseCreationOptions.ToolChoice,
                Temperature = responseAgentInvokeOptions.ResponseCreationOptions.Temperature,
                TopP = responseAgentInvokeOptions.ResponseCreationOptions.TopP,
                PreviousResponseId = responseAgentInvokeOptions.ResponseCreationOptions.PreviousResponseId,
            };
            creationOptions.Tools.AddRange(responseAgentInvokeOptions.ResponseCreationOptions.Tools);
            responseAgentInvokeOptions.ResponseCreationOptions.Metadata.ToList().ForEach(kvp => creationOptions.Metadata[kvp.Key] = kvp.Value);
        }
        else
        {
            creationOptions = new CreateResponseOptions
            {
                EndUserId = agent.GetDisplayName(),
                Instructions = instructions,
                StoredOutputEnabled = agent.StoreEnabled,
            };
        }

        if (agent.StoreEnabled && agentThread.Id is not null)
        {
            creationOptions.PreviousResponseId = agentThread.Id;
        }

        var responseTools = agent.GetKernel(invokeOptions).Plugins
            .SelectMany(kp => kp.Select(kf => kf.ToResponseTool(kp.Name)));
        if (responseTools is not null && responseTools.Any())
        {
            creationOptions.Tools.AddRange(responseTools);
            if (creationOptions.ToolChoice is null)
            {
                creationOptions.ToolChoice = ResponseToolChoice.CreateAutoChoice();
            }
        }

        return creationOptions;
    }
}
