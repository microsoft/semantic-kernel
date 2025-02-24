// Copyright (c) Microsoft. All rights reserved.

using Azure.AI.Projects;

namespace Microsoft.SemanticKernel.Agents.AzureAI;

/// <summary>
/// Provides extension methods for <see cref="AgentToolDefinition"/>.
/// </summary>
internal static class AgentToolDefinitionExtensions
{
    internal static AzureFunctionBinding GetInputBinding(this AgentToolDefinition agentToolDefinition)
    {
        Verify.NotNull(agentToolDefinition.Configuration);

        string storageServiceEndpoint;
        string queueName;

        return new AzureFunctionBinding(new AzureFunctionStorageQueue(storageServiceEndpoint, queueName));
    }
}
