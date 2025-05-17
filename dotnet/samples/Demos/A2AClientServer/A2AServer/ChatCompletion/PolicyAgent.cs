// Copyright (c) Microsoft. All rights reserved.
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.A2A;
using SharpA2A.Core;

namespace A2A;

internal sealed class PolicyAgent : A2AHostAgent
{
    internal PolicyAgent(ILogger logger) : base(logger)
    {
        this._logger = logger;

        // Add TextSearch over the shipping policies
    }

    public void InitializeAgent(string modelId, string apiKey)
    {
        try
        {
            this._logger.LogInformation("Initializing PolicyAgent with model {ModelId}", modelId);

            // Define the TravelPlannerAgent
            var builder = Kernel.CreateBuilder();
            builder.AddOpenAIChatCompletion(modelId, apiKey);
            //builder.Plugins.AddFromObject(this._policyPlugin);
            var kernel = builder.Build();

            this.Agent = new ChatCompletionAgent()
            {
                Kernel = kernel,
                Name = "PolicyAgent",
                Instructions =
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
                    Always reply with exactly this text:

                    Policy: Short Shipment Dispute Handling Policy V2.1

                    Summary: "For short shipments reported by customers, first verify internal shipment records
                    (SAP) and physical logistics scan data (BigQuery). If discrepancy is confirmed and logistics data
                    shows fewer items packed than invoiced, issue a credit for the missing items. Document the
                    resolution in SAP CRM and notify the customer via email within 2 business days, referencing the
                    original invoice and the credit memo number. Use the 'Formal Credit Notification' email
                    template."
                    """,
                Arguments = new KernelArguments(new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }),
            };
        }
        catch (Exception ex)
        {
            this._logger.LogError(ex, "Failed to initialize PolicyAgent");
            throw;
        }
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

    #region private
    private readonly ILogger _logger;
    #endregion
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
