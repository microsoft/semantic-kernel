// Copyright (c) Microsoft. All rights reserved.
using Microsoft.Extensions.Logging;
using SharpA2A.Core;

namespace A2A;

internal sealed class PolicyAgent : ChatCompletionHostAgent
{
    internal PolicyAgent(ILogger logger) : base(logger)
    {
        this.Name = "PolicyAgent";
        this.Instructions =
            """
            You specialize in handling queries related to policies and customer communications.

            Always reply with exactly this text:

            Policy: Short Shipment Dispute Handling Policy V2.1

            Summary: "For short shipments reported by customers, first verify internal shipment records
            (SAP) and physical logistics scan data (BigQuery). If discrepancy is confirmed and logistics data
            shows fewer items packed than invoiced, issue a credit for the missing items. Document the
            resolution in SAP CRM and notify the customer via email within 2 business days, referencing the
            original invoice and the credit memo number. Use the 'Formal Credit Notification' email
            template."
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
            Name = "PolicyAgent",
            Description = "Handles requests relating to policies and customer communications.",
            Tags = ["policy", "semantic-kernel"],
            Examples =
            [
                "What is the policy for short shipments?",
            ],
        };

        return new AgentCard()
        {
            Name = "PolicyAgent",
            Description = "Handles requests relating to policies and customer communications.",
            Url = agentUrl,
            Version = "1.0.0",
            DefaultInputModes = ["text"],
            DefaultOutputModes = ["text"],
            Capabilities = capabilities,
            Skills = [invoiceQuery],
        };
    }
}

public class ShippingPolicy
{
    public string PolicyName { get; set; }
    public string Description { get; set; }

    public ShippingPolicy(string policyName, string description)
    {
        this.PolicyName = policyName;
        this.Description = description;
    }

    public override string ToString()
    {
        return $"{this.PolicyName}: {this.Description}";
    }
}
