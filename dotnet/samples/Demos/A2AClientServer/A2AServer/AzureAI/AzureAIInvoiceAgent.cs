// Copyright (c) Microsoft. All rights reserved.
using Azure.AI.Agents.Persistent;
using Azure.Identity;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.A2A;
using Microsoft.SemanticKernel.Agents.AzureAI;
using SharpA2A.Core;

namespace A2A;

internal sealed class AzureAIInvoiceAgent : A2AHostAgent
{
    internal AzureAIInvoiceAgent(ILogger logger) : base(logger)
    {
        this._logger = logger;
    }

    public async Task InitializeAgentAsync(string modelId, string endpoint, string assistantId)
    {
        try
        {
            this._logger.LogInformation("Initializing AzureAIInvoiceAgent {AssistantId}", assistantId);

            // Define the InvoiceAgent
            var agentsClient = new PersistentAgentsClient(endpoint, new AzureCliCredential());
            PersistentAgent definition = await agentsClient.Administration.GetAgentAsync(assistantId);

            this.Agent = new AzureAIAgent(definition, agentsClient);
            this.Agent.Kernel.Plugins.Add(KernelPluginFactory.CreateFromType<InvoiceQueryPlugin>());
        }
        catch (Exception ex)
        {
            this._logger.LogError(ex, "Failed to initialize AzureAIInvoiceAgent");
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
            Name = "InvoiceQuery",
            Description = "Handles requests relating to invoices.",
            Tags = ["invoice", "semantic-kernel"],
            Examples =
            [
                "List the latest invoices for Contoso.",
            ],
        };

        return new AgentCard()
        {
            Name = this.Agent.Name ?? "InvoiceAgent",
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
