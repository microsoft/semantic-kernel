// Copyright (c) Microsoft. All rights reserved.
using Azure.AI.Agents.Persistent;
using Azure.Identity;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.A2A;
using Microsoft.SemanticKernel.Agents.AzureAI;
using SharpA2A.Core;

namespace A2A;

internal sealed class AzureAILogisticsAgent : A2AHostAgent
{
    internal AzureAILogisticsAgent(ILogger logger) : base(logger)
    {
        this._logger = logger;
    }

    public async Task InitializeAgentAsync(string modelId, string endpoint, string assistantId)
    {
        try
        {
            this._logger.LogInformation("Initializing AzureAILogisticsAgent {AssistantId}", assistantId);

            // Define the InvoiceAgent
            var agentsClient = new PersistentAgentsClient(endpoint, new AzureCliCredential());
            PersistentAgent definition = await agentsClient.Administration.GetAgentAsync(assistantId);

            this.Agent = new AzureAIAgent(definition, agentsClient);
        }
        catch (Exception ex)
        {
            this._logger.LogError(ex, "Failed to initialize AzureAILogisticsAgent");
            throw;
        }
    }

    public override AgentCard GetAgentCard(string agentUrl)
    {
        if (this.Agent is null)
        {
            throw new InvalidOperationException("Agent not initialized.");
        }

        var capabilities = new AgentCapabilities()
        {
            Streaming = false,
            PushNotifications = false,
        };

        var invoiceQuery = new AgentSkill()
        {
            Id = "id_invoice_agent",
            Name = "LogisticsQuery",
            Description = "Handles requests relating to logistics.",
            Tags = ["logistics", "semantic-kernel"],
            Examples =
            [
                "What is the status for SHPMT-SAP-001",
            ],
        };

        return new AgentCard()
        {
            Name = this.Agent.Name ?? "LogisticsAgent",
            Description = this.Agent.Description,
            Url = agentUrl,
            Version = "1.0.0",
            DefaultInputModes = ["text"],
            DefaultOutputModes = ["text"],
            Capabilities = capabilities,
            Skills = [invoiceQuery],
        };
    }

    #region private
    private readonly ILogger _logger;
    #endregion
}
