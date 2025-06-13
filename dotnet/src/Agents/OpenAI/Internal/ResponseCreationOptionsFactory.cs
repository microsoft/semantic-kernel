// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using Microsoft.SemanticKernel.Agents.Extensions;
using OpenAI.Responses;

namespace Microsoft.SemanticKernel.Agents.OpenAI.Internal;

/// <summary>
/// Factory for creating instances of <see cref="ResponseCreationOptions"/>.
/// </summary>
internal static class ResponseCreationOptionsFactory
{
    internal static ResponseCreationOptions CreateOptions(
        OpenAIResponseAgent agent,
        AgentThread agentThread,
        AgentInvokeOptions? invokeOptions)
    {
        if (invokeOptions is OpenAIResponseAgentInvokeOptions responseAgentInvokeOptions &&
            responseAgentInvokeOptions.ResponseCreationOptions is not null)
        {
            // Use the options provided by the caller
            return responseAgentInvokeOptions.ResponseCreationOptions;
        }

        var responseTools = invokeOptions.GetKernel(agent).Plugins
            .SelectMany(kp => kp.Select(kf => kf.ToResponseTool(kp.Name)));

        var creationOptions = new ResponseCreationOptions
        {
            EndUserId = agent.GetDisplayName(),
            Instructions = $"{agent.Instructions}\n{invokeOptions?.AdditionalInstructions}",
            StoredOutputEnabled = agent.StoreEnabled,
        };

        if (agent.StoreEnabled && agentThread.Id is not null)
        {
            creationOptions.PreviousResponseId = agentThread.Id;
        }

        if (responseTools is not null && responseTools.Any())
        {
            creationOptions.Tools.AddRange(responseTools);
            creationOptions.ToolChoice = ResponseToolChoice.CreateAutoChoice();
            creationOptions.ParallelToolCallsEnabled = true;
        }

        return creationOptions;
    }
}
