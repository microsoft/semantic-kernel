// Copyright (c) Microsoft. All rights reserved.
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using SharpA2A.Core;

namespace A2A;

internal sealed class InvoiceAgent : ChatCompletionHostAgent
{
    internal InvoiceAgent(ILogger logger) : base(logger)
    {
        this.Name = "InvoiceAgent";
        this.Instructions = "You specialize in handling queries related to invoices.";
        this.Plugins = [KernelPluginFactory.CreateFromType<InvoiceQueryPlugin>()];
    }

    public override AgentCard GetAgentCard(string agentUrl)
    {
        var capabilities = new AgentCapabilities()
        {
            Streaming = false,
            PushNotifications = false,
        };

        var invoiceQuery = new AgentSkill()
        {
            Id = "id_invoice_agent",
            Name = "InvoiceAgent",
            Description = "Handles requests relating to invoices.",
            Tags = ["invoice", "semantic-kernel"],
            Examples =
            [
                "List the latest invoices for Contoso.",
            ],
        };

        return new AgentCard()
        {
            Name = "InvoiceAgent",
            Description = "Handles requests relating to invoices.",
            Url = agentUrl,
            Version = "1.0.0",
            DefaultInputModes = ["text"],
            DefaultOutputModes = ["text"],
            Capabilities = capabilities,
            Skills = [invoiceQuery],
        };
    }
}
