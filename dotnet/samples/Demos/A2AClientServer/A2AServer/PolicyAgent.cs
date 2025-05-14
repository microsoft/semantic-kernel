// Copyright (c) Microsoft. All rights reserved.
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.A2A;
using SharpA2A.Core;

namespace A2A;

internal sealed class PolicyAgent : A2AHostAgent
{
    internal PolicyAgent(string modelId, string apiKey, ILogger logger) : base(logger)
    {
        this._logger = logger;

        // Add TextSearch over the shipping policies

        this.Agent = this.InitializeAgent(modelId, apiKey);
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

    private ChatCompletionAgent InitializeAgent(string modelId, string apiKey)
    {
        try
        {
            this._logger.LogInformation("Initializing Semantic Kernel agent with model {ModelId}", modelId);

            // Define the TravelPlannerAgent
            var builder = Kernel.CreateBuilder();
            builder.AddOpenAIChatCompletion(modelId, apiKey);
            //builder.Plugins.AddFromObject(this._policyPlugin);
            var kernel = builder.Build();
            return new ChatCompletionAgent()
            {
                Kernel = kernel,
                Name = "PolicyAgent",
                Instructions =
                    """
                    You specialize in handling queries related to policies and customer communications.
                    """,
                Arguments = new KernelArguments(new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }),
            };
        }
        catch (Exception ex)
        {
            this._logger.LogError(ex, "Failed to initialize InvoiceAgent");
            throw;
        }
    }
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

public class ShippingPolicies
{
    private readonly List<ShippingPolicy> _policies;

    public ShippingPolicies()
    {
        this._policies = new List<ShippingPolicy>
        {
            new ("Late Shipments", "If a shipment is not delivered by the expected delivery date, customers will be notified and offered a discount on their next order."),
            new ("Missing Shipments", "In cases where a shipment is reported missing, an investigation will be initiated within 48 hours, and a replacement will be sent if necessary."),
            new ("Short Shipments", "If a shipment arrives with missing items, customers should report it within 7 days for a full refund or replacement."),
            new ("Damaged Goods", "If goods are received damaged, customers must report the issue within 48 hours. A replacement or refund will be offered after inspection."),
            new ("Return Policy", "Customers can return items within 30 days of receipt for a full refund, provided they are in original condition."),
            new ("Delivery Area Limitations", "We currently only ship to specific regions. Please check our website for a list of eligible shipping areas."),
            new ("International Shipping", "International shipments may be subject to customs duties and taxes, which are the responsibility of the customer.")
        };
    }

    public List<ShippingPolicy> GetPolicies => this._policies;

    public void AddPolicy(ShippingPolicy policy)
    {
        this._policies.Add(policy);
    }
}
