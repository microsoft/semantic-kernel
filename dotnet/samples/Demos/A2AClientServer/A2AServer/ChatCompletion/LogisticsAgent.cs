// Copyright (c) Microsoft. All rights reserved.
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.A2A;
using SharpA2A.Core;

namespace A2A;

internal sealed class LogisticsAgent : A2AHostAgent
{
    internal LogisticsAgent(ILogger logger) : base(logger)
    {
        this._logger = logger;

        // Add TextSearch over the shipping policies
    }

    public void InitializeAgent(string modelId, string apiKey)
    {
        try
        {
            this._logger.LogInformation("Initializing LogisticAgent with model {ModelId}", modelId);

            // Define the TravelPlannerAgent
            var builder = Kernel.CreateBuilder();
            builder.AddOpenAIChatCompletion(modelId, apiKey);
            var kernel = builder.Build();

            this.Agent = new ChatCompletionAgent()
            {
                Kernel = kernel,
                Name = "LogisticsAgent",
                Instructions =
                    """
                    You specialize in handling queries related to logistics

                    Always reply with exactly:

                    Shipment number: SHPMT-SAP-001
                    Item: TSHIRT-RED-L
                    Quantity: 900                    
                    """,
                Arguments = new KernelArguments(new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }),
            };
        }
        catch (Exception ex)
        {
            this._logger.LogError(ex, "Failed to initialize LogisticAgent");
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

    #region private
    private readonly ILogger _logger;
    #endregion
}
