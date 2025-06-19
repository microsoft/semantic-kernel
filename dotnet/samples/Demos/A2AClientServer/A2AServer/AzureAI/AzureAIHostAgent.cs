// Copyright (c) Microsoft. All rights reserved.

using Azure.AI.Agents.Persistent;
using Azure.Identity;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.A2A;
using Microsoft.SemanticKernel.Agents.AzureAI;

namespace A2A;

internal abstract class AzureAIHostAgent : A2AHostAgent
{
    /// <summary>
    /// Optional: The plugins associated with the agent.
    /// </summary>
    protected IEnumerable<KernelPlugin>? Plugins { get; set; }

    internal AzureAIHostAgent(ILogger logger) : base(logger)
    {
        this._logger = logger;
    }

    public async Task InitializeAgentAsync(string modelId, string endpoint, string assistantId)
    {
        try
        {
            this._logger.LogInformation("Initializing AzureAIPolicyAgent {AssistantId}", assistantId);

            // Define the InvoiceAgent
            var agentsClient = new PersistentAgentsClient(endpoint, new AzureCliCredential());
            PersistentAgent definition = await agentsClient.Administration.GetAgentAsync(assistantId);

            this.Agent = new AzureAIAgent(definition, agentsClient, this.Plugins);
        }
        catch (Exception ex)
        {
            this._logger.LogError(ex, "Failed to initialize AzureAIHostAgent");
            throw;
        }
    }

    #region private
    private readonly ILogger _logger;
    #endregion
}
