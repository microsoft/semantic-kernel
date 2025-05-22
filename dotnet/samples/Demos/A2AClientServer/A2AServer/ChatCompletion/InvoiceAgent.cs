// Copyright (c) Microsoft. All rights reserved.
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.A2A;
using SharpA2A.Core;

namespace A2A;

internal sealed class InvoiceAgent : A2AHostAgent
{
    internal InvoiceAgent(ILogger logger) : base(logger)
    {
        this._logger = logger;
    }

    public void InitializeAgent(string modelId, string apiKey)
    {
        try
        {
            this._logger.LogInformation("Initializing InvoiceAgent with model {ModelId}", modelId);

            // Define the InvoiceAgent
            var builder = Kernel.CreateBuilder();
            builder.AddOpenAIChatCompletion(modelId, apiKey);
            builder.Plugins.AddFromType<InvoiceQueryPlugin>();
            var kernel = builder.Build();

            this.Agent = new ChatCompletionAgent()
            {
                Kernel = kernel,
                Name = "InvoiceAgent",
                Instructions =
                    """
                    You specialize in handling queries related to invoices.
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

    #region private
    private readonly ILogger _logger;
    #endregion
}
