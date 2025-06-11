// Copyright (c) Microsoft. All rights reserved.
using Azure.AI.Agents.Persistent;
using Azure.Identity;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.A2A;
using Microsoft.SemanticKernel.Agents.AzureAI;
using SharpA2A.Core;

namespace A2A;

internal sealed class AzureAICurrencyAgent : A2AHostAgent, IDisposable
{
    internal AzureAICurrencyAgent(ILogger logger) : base(logger)
    {
        this._logger = logger;
        this._httpClient = new HttpClient();

        this._currencyPlugin = new CurrencyPlugin(
            logger: new Logger<CurrencyPlugin>(new LoggerFactory()),
            httpClient: this._httpClient);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();

        if (this.Agent is AzureAIAgent azureAIAgent && azureAIAgent is not null)
        {
            azureAIAgent.Client.Administration.DeleteAgent(azureAIAgent.Id);
        }
    }

    public async Task InitializeAgentAsync(string modelId, string endpoint)
    {
        try
        {
            this._logger.LogInformation("Initializing Semantic Kernel agent with model {ModelId}", modelId);

            // Define the CurrencyAgent
            var agentsClient = new PersistentAgentsClient(endpoint, new AzureCliCredential());
            PersistentAgent definition = await agentsClient.Administration.CreateAgentAsync(
                modelId,
                "CurrencyAgent",
                null,
                """
                    You specialize in handling queries related to currency exchange rates.
                """);

            this.Agent = new AzureAIAgent(definition, agentsClient);

            if (this._currencyPlugin is not null)
            {
                this.Agent.Kernel.Plugins.Add(KernelPluginFactory.CreateFromObject(this._currencyPlugin));
            }
        }
        catch (Exception ex)
        {
            this._logger.LogError(ex, "Failed to initialize AzureAICurrencyAgent");
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
            Id = "id_currency_agent",
            Name = "CurrencyAgent",
            Description = "Handles requests relating to currency exchange.",
            Tags = ["currency", "semantic-kernel"],
            Examples =
            [
                "What is the current exchange rather for Dollars to Euro?",
            ],
        };

        return new AgentCard()
        {
            Name = "CurrencyAgent",
            Description = "Handles requests relating to currency exchange.",
            Url = agentUrl,
            Version = "1.0.0",
            DefaultInputModes = ["text"],
            DefaultOutputModes = ["text"],
            Capabilities = capabilities,
            Skills = [invoiceQuery],
        };
    }

    #region private
    private readonly CurrencyPlugin _currencyPlugin;
    private readonly HttpClient _httpClient;
    private readonly ILogger _logger;

    #endregion
}
