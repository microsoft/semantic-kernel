// Copyright (c) Microsoft. All rights reserved.

using Azure;
using System;
using Microsoft.Extensions.DependencyInjection;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.Agents;

namespace Microsoft.SemanticKernel.Process.Internal;

/// <summary>
/// A factory for creating agent threads.
/// </summary>
public static class AgentThreadFactory
{
    /// <summary>
    /// Processes the thread definition and creates an underlying thread if needed.
    /// </summary>
    /// <param name="threadDefinition"></param>
    /// <param name="kernel"></param>
    /// <returns></returns>
    /// <exception cref="KernelException"></exception>
    public static async Task<AgentThread> CreateAgentThreadAsync(this KernelProcessAgentThread threadDefinition, Kernel kernel)
    {
        switch (threadDefinition.ThreadType)
        {
            case KernelProcessThreadType.AzureAI:
                return await CreateAzureAIThreadAsync(threadDefinition.ThreadId, kernel).ConfigureAwait(false);

            default:
                throw new KernelException($"Thread type {threadDefinition.ThreadType} is not supported.");

        }
    }

    private static async Task<AgentThread> CreateAzureAIThreadAsync(string? id, Kernel kernel)
    {
        const string ErrorMessage = "The thread could not be created due to an error response from the service.";
        var client = kernel.Services.GetService<Azure.AI.Projects.AgentsClient>() ?? throw new KernelException("The AzureAI thread type requires an AgentsClient to be registered in the kernel.");

        if (string.IsNullOrWhiteSpace(id))
        {
            try
            {
                var threadResponse = await client.CreateThreadAsync().ConfigureAwait(false);
                id = threadResponse.Value.Id;
            }
            catch (RequestFailedException ex)
            {
                throw new KernelException(ErrorMessage, ex);
            }
            catch (AggregateException ex)
            {
                throw new KernelException(ErrorMessage, ex);
            }
        }

        return new AzureAIAgentThread(client, id);
    }
}
