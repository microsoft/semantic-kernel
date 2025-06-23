// Copyright (c) Microsoft. All rights reserved.

using Azure.AI.Agents.Persistent;
using Azure.Identity;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.A2A;
using Microsoft.SemanticKernel.Agents.AzureAI;
using SharpA2A.Core;

namespace A2AServer;

internal static class HostAgentFactory
{
    internal static async Task<A2AHostAgent> CreateFoundryHostAgentAsync(string agentType, string modelId, string endpoint, string assistantId, IEnumerable<KernelPlugin>? plugins = null)
    {
        var agentsClient = new PersistentAgentsClient(endpoint, new AzureCliCredential());
        PersistentAgent definition = await agentsClient.Administration.GetAgentAsync(assistantId);

        var agent = new AzureAIAgent(definition, agentsClient, plugins);

        AgentCard agentCard = agentType.ToUpperInvariant() switch
        {
            "INVOICE" => GetInvoiceAgentCard(),
            "POLICY" => GetPolicyAgentCard(),
            "LOGISTICS" => GetLogisticsAgentCard(),
            _ => throw new ArgumentException($"Unsupported agent type: {agentType}"),
        };

        return new A2AHostAgent(agent, agentCard);
    }

    internal static async Task<A2AHostAgent> CreateChatCompletionHostAgentAsync(string agentType, string modelId, string apiKey, string name, string instructions, IEnumerable<KernelPlugin>? plugins = null)
    {
        var builder = Kernel.CreateBuilder();
        builder.AddOpenAIChatCompletion(modelId, apiKey);
        if (plugins is not null)
        {
            foreach (var plugin in plugins)
            {
                builder.Plugins.Add(plugin);
            }
        }
        var kernel = builder.Build();

        var agent = new ChatCompletionAgent()
        {
            Kernel = kernel,
            Name = name,
            Instructions = instructions,
            Arguments = new KernelArguments(new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }),
        };

        AgentCard agentCard = agentType.ToUpperInvariant() switch
        {
            "INVOICE" => GetInvoiceAgentCard(),
            "POLICY" => GetPolicyAgentCard(),
            "LOGISTICS" => GetLogisticsAgentCard(),
            _ => throw new ArgumentException($"Unsupported agent type: {agentType}"),
        };

        return new A2AHostAgent(agent, agentCard);
    }

    #region private
    private static AgentCard GetInvoiceAgentCard()
    {
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
            Name = "InvoiceAgent",
            Description = "Handles requests relating to invoices.",
            Version = "1.0.0",
            DefaultInputModes = ["text"],
            DefaultOutputModes = ["text"],
            Capabilities = capabilities,
            Skills = [invoiceQuery],
        };
    }

    private static AgentCard GetPolicyAgentCard()
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
            Version = "1.0.0",
            DefaultInputModes = ["text"],
            DefaultOutputModes = ["text"],
            Capabilities = capabilities,
            Skills = [invoiceQuery],
        };
    }

    private static AgentCard GetLogisticsAgentCard()
    {
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
            Name = "LogisticsAgent",
            Description = agent.Description,
            Version = "1.0.0",
            DefaultInputModes = ["text"],
            DefaultOutputModes = ["text"],
            Capabilities = capabilities,
            Skills = [invoiceQuery],
        };
    }
    #endregion
}
