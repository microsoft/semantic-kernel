// Copyright (c) Microsoft. All rights reserved.
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.A2A;
using SharpA2A.Core;

namespace A2A;

internal sealed class CurrencyAgent : A2AHostAgent, IDisposable
{
    internal CurrencyAgent(ILogger logger) : base(logger)
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
    }
    public void InitializeAgent(string modelId, string apiKey)
    {
        try
        {
            this._logger.LogInformation("Initializing CurrencyAgent with model {ModelId}", modelId);

            // Define the CurrencyAgent
            var builder = Kernel.CreateBuilder();
            builder.AddOpenAIChatCompletion(modelId, apiKey);
            builder.Plugins.AddFromObject(this._currencyPlugin);
            var kernel = builder.Build();

            this.Agent = new ChatCompletionAgent()
            {
                Kernel = kernel,
                Name = "CurrencyAgent",
                Instructions =
                    """
                    You specialize in handling queries related to currency exchange rates.
                    """,
                Arguments = new KernelArguments(new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }),
            };
        }
        catch (Exception ex)
        {
            this._logger.LogError(ex, "Failed to initialize CurrencyAgent");
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
