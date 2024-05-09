// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;

namespace Filtering;

public class PIIDetectionWithFilters(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task PIIAnalyzerAsync()
    {
        var builder = Kernel.CreateBuilder();

        // Add Azure OpenAI chat completion service
        builder.AddAzureOpenAIChatCompletion(
            TestConfiguration.AzureOpenAI.ChatDeploymentName,
            TestConfiguration.AzureOpenAI.Endpoint,
            TestConfiguration.AzureOpenAI.ApiKey);

        // Add logging
        var logger = this.LoggerFactory.CreateLogger<PIIDetectionWithFilters>();
        builder.Services.AddSingleton<ILogger>(logger);

        // Add Microsoft Presidio Text Analyzer service and configure HTTP client for it
        builder.Services.AddHttpClient<PresidioTextAnalyzerService>(client =>
        {
            client.BaseAddress = new Uri("http://localhost:5001");
        });

        // Add prompt filter to analyze rendered prompt for PII before sending it to LLM
        builder.Services.AddSingleton<IPromptRenderFilter, PIIAnalyzerFilter>();

        var kernel = builder.Build();

        var result1 = await kernel.InvokePromptAsync("John Smith drivers license is AC432223");
        logger.LogInformation("Result: {Result}", result1.ToString());

        /* 
        Prompt: John Smith drivers license is AC432223
        Entity type: PERSON. Score: 0.85
        Entity type: US_DRIVER_LICENSE. Score: 0.6499999999999999
        Result: Prompt contains PII information. Operation is canceled. 
        */

        var result2 = await kernel.InvokePromptAsync("Hi, can you help me?");
        logger.LogInformation("Result: {Result}", result2.ToString());

        /*
        Prompt: Hi, can you help me?
        Result: Of course! I'm here to help. What do you need assistance with?
        */
    }

    #region Filters

    private sealed class PIIAnalyzerFilter(ILogger logger, PresidioTextAnalyzerService analyzer) : IPromptRenderFilter
    {
        public async Task OnPromptRenderAsync(PromptRenderContext context, Func<PromptRenderContext, Task> next)
        {
            await next(context);

            var prompt = context.RenderedPrompt!;

            logger.LogTrace("Prompt: {Prompt}", prompt);

            var analyzerResult = await analyzer.AnalyzeAsync(new PresidioTextAnalyzerRequest { Text = prompt });

            var piiDetected = false;

            foreach (var result in analyzerResult)
            {
                logger.LogInformation("Entity type: {EntityType}. Score: {Score}", result.EntityType, result.Score);

                if (result.Score > 0.5)
                {
                    piiDetected = true;
                }
            }

            if (piiDetected)
            {
                context.Result = new FunctionResult(context.Function, "Prompt contains PII information. Operation is canceled.");
            }
        }
    }

    #endregion

    #region Microsoft Presidio Text Analyzer

    private sealed class PresidioTextAnalyzerRequest
    {
        /// <summary>The text to analyze.</summary>
        [JsonPropertyName("text")]
        public string Text { get; set; }

        /// <summary>Two characters for the desired language in ISO_639-1 format.</summary>
        [JsonPropertyName("language")]
        public string Language { get; set; } = "en";
    }

    private sealed class PresidioTextAnalyzerResponse
    {
        /// <summary>Where the PII starts.</summary>
        [JsonPropertyName("start")]
        public int Start { get; set; }

        /// <summary>Where the PII ends.</summary>
        [JsonPropertyName("end")]
        public int End { get; set; }

        /// <summary>The PII detection score from 0 to 1.</summary>
        [JsonPropertyName("score")]
        public double Score { get; set; }

        /// <summary>The supported PII entity types.</summary>
        [JsonPropertyName("entity_type")]
        public string EntityType { get; set; }
    }

    private sealed class PresidioTextAnalyzerService(HttpClient httpClient)
    {
        private const string RequestUri = "analyze";

        public async Task<List<PresidioTextAnalyzerResponse>> AnalyzeAsync(PresidioTextAnalyzerRequest request)
        {
            var requestContent = new StringContent(JsonSerializer.Serialize(request), Encoding.UTF8, "application/json");

            var response = await httpClient.PostAsync(new Uri(RequestUri, UriKind.Relative), requestContent);

            response.EnsureSuccessStatusCode();

            var responseContent = await response.Content.ReadAsStringAsync();

            return JsonSerializer.Deserialize<List<PresidioTextAnalyzerResponse>>(responseContent) ??
                throw new Exception("Analyzer response is not available.");
        }
    }

    #endregion
}
