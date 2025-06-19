// Copyright (c) Microsoft. All rights reserved.
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using SharpA2A.Core;

namespace A2A;

internal sealed class AzureAIInvoiceAgent : AzureAIHostAgent
{
    internal AzureAIInvoiceAgent(ILogger logger) : base(logger)
    {
        this.Plugins = [KernelPluginFactory.CreateFromType<InvoiceQueryPlugin>()];
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
}
