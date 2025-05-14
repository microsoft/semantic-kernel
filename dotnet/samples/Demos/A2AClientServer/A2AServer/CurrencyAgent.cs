// Copyright (c) Microsoft. All rights reserved.
using System.ComponentModel;
using System.Text.Json;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.A2A;
using Polly;
using Polly.Retry;
using SharpA2A.Core;

namespace A2A;

internal sealed class CurrencyAgent : A2AHostAgent, IDisposable
{
    internal CurrencyAgent(string modelId, string apiKey, ILogger logger) : base(logger)
    {
        this._logger = logger;
        this._httpClient = new HttpClient();

        this._currencyPlugin = new CurrencyPlugin(
            logger: new Logger<CurrencyPlugin>(new LoggerFactory()),
            httpClient: this._httpClient);

        this.Agent = this.InitializeAgent(modelId, apiKey);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
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

    private ChatCompletionAgent InitializeAgent(string modelId, string apiKey)
    {
        try
        {
            this._logger.LogInformation("Initializing Semantic Kernel agent with model {ModelId}", modelId);

            // Define the TravelPlannerAgent
            var builder = Kernel.CreateBuilder();
            builder.AddOpenAIChatCompletion(modelId, apiKey);
            builder.Plugins.AddFromObject(this._currencyPlugin);
            var kernel = builder.Build();
            return new ChatCompletionAgent()
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
            this._logger.LogError(ex, "Failed to initialize InvoiceAgent");
            throw;
        }
    }
    #endregion
}

/// <summary>
/// A simple currency plugin that leverages Frankfurter for exchange rates.
/// The Plugin is used by the currency_exchange_agent.
/// </summary>
public class CurrencyPlugin
{
    private readonly ILogger<CurrencyPlugin> _logger;
    private readonly HttpClient _httpClient;
    private readonly AsyncRetryPolicy<HttpResponseMessage> _retryPolicy;

    /// <summary>
    /// Initialize a new instance of the CurrencyPlugin
    /// </summary>
    /// <param name="logger">Logger for the plugin</param>
    /// <param name="httpClient">HTTP client factory for making API requests</param>
    public CurrencyPlugin(ILogger<CurrencyPlugin> logger, HttpClient httpClient)
    {
        this._logger = logger ?? throw new ArgumentNullException(nameof(logger));
        this._httpClient = httpClient ?? throw new ArgumentNullException(nameof(httpClient));

        // Create a retry policy for transient HTTP errors
        this._retryPolicy = Policy
            .HandleResult<HttpResponseMessage>(r => !r.IsSuccessStatusCode && this.IsTransientError(r))
            .WaitAndRetryAsync(3, retryAttempt => TimeSpan.FromSeconds(Math.Pow(2, retryAttempt)));
    }

    /// <summary>
    /// Retrieves exchange rate between currency_from and currency_to using Frankfurter API
    /// </summary>
    /// <param name="currencyFrom">Currency code to convert from, e.g. USD</param>
    /// <param name="currencyTo">Currency code to convert to, e.g. EUR or INR</param>
    /// <param name="date">Date or 'latest'</param>
    /// <returns>String representation of exchange rate</returns>
    [KernelFunction]
    [Description("Retrieves exchange rate between currency_from and currency_to using Frankfurter API")]
    public async Task<string> GetExchangeRateAsync(
        [Description("Currency code to convert from, e.g. USD")] string currencyFrom,
        [Description("Currency code to convert to, e.g. EUR or INR")] string currencyTo,
        [Description("Date or 'latest'")] string date = "latest")
    {
        try
        {
            this._logger.LogInformation("Getting exchange rate from {CurrencyFrom} to {CurrencyTo} for date {Date}",
                currencyFrom, currencyTo, date);

            // Build request URL with query parameters
            var requestUri = new Uri($"https://api.frankfurter.app/{date}?from={Uri.EscapeDataString(currencyFrom)}&to={Uri.EscapeDataString(currencyTo)}");

            // Use retry policy for resilience
            var response = await this._retryPolicy.ExecuteAsync(() => this._httpClient.GetAsync(requestUri)).ConfigureAwait(false);
            response.EnsureSuccessStatusCode();

            var jsonContent = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
            var data = JsonSerializer.Deserialize<JsonElement>(jsonContent);

            if (!data.TryGetProperty("rates", out var rates) ||
                !rates.TryGetProperty(currencyTo, out var rate))
            {
                this._logger.LogWarning("Could not retrieve rate for {CurrencyFrom} to {CurrencyTo}", currencyFrom, currencyTo);
                return $"Could not retrieve rate for {currencyFrom} to {currencyTo}";
            }

            return $"1 {currencyFrom} = {rate.GetDecimal()} {currencyTo}";
        }
        catch (Exception ex)
        {
            this._logger.LogError(ex, "Error getting exchange rate from {CurrencyFrom} to {CurrencyTo}", currencyFrom, currencyTo);
            return $"Currency API call failed: {ex.Message}";
        }
    }

    /// <summary>
    /// Checks if the HTTP response indicates a transient error
    /// </summary>
    /// <param name="response">HTTP response message</param>
    /// <returns>True if the status code indicates a transient error</returns>
    private bool IsTransientError(HttpResponseMessage response)
    {
        int statusCode = (int)response.StatusCode;
        return statusCode == 408 // Request Timeout
            || statusCode == 429 // Too Many Requests 
            || statusCode >= 500 && statusCode < 600; // Server errors
    }
}
