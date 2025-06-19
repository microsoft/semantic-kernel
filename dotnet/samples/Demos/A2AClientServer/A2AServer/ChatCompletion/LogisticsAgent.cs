// Copyright (c) Microsoft. All rights reserved.
using Microsoft.Extensions.Logging;
using SharpA2A.Core;

namespace A2A;

internal sealed class LogisticsAgent : ChatCompletionHostAgent
{
    internal LogisticsAgent(ILogger logger) : base(logger)
    {
        this.Name = "LogisticsAgent";
        this.Instructions =
            """
            You specialize in handling queries related to logistics.

            Always reply with exactly:

            Shipment number: SHPMT-SAP-001
            Item: TSHIRT-RED-L
            Quantity: 900                    
            """;
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
            Id = "id_policy_agent",
            Name = "LogisticsAgent",
            Description = "Handles requests relating to logistics.",
            Tags = ["logistics", "semantic-kernel"],
            Examples =
            [
                "What is the status for SHPMT-SAP-001",
            ],
        };

        return new AgentCard()
        {
            Name = "LogisticsAgent",
            Description = "Handles requests relating to logistics.",
            Url = agentUrl,
            Version = "1.0.0",
            DefaultInputModes = ["text"],
            DefaultOutputModes = ["text"],
            Capabilities = capabilities,
            Skills = [invoiceQuery],
        };
    }
}
