// Copyright (c) Microsoft. All rights reserved.
using Microsoft.Extensions.Logging;
using SharpA2A.Core;

namespace A2A;

internal sealed class AzureAILogisticsAgent : AzureAIHostAgent
{
    internal AzureAILogisticsAgent(ILogger logger) : base(logger)
    {
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
}
