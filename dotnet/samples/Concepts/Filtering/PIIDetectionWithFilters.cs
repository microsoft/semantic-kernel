// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace Filtering;

public class PIIDetectionWithFilters(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task PromptAnalyzerAsync()
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
        builder.Services.AddHttpClient<PresidioTextAnalyzerService>(client => { client.BaseAddress = new Uri("http://localhost:5001"); });

        // Add prompt filter to analyze rendered prompt for PII before sending it to LLM
        builder.Services.AddSingleton<IPromptRenderFilter, PromptAnalyzerFilter>();

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

    [Fact]
    public async Task PromptAnonymizerAsync()
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
        builder.Services.AddHttpClient<PresidioTextAnalyzerService>(client => { client.BaseAddress = new Uri("http://localhost:5001"); });

        // Add Microsoft Presidio Text Anonymizer service and configure HTTP client for it
        builder.Services.AddHttpClient<PresidioTextAnonymizerService>(client => { client.BaseAddress = new Uri("http://localhost:5002"); });

        // Define anonymizer rules: redact phone number, and replace person name with word "ANONYMIZED"
        var anonymizers = new Dictionary<string, PresidioTextAnonymizer>
        {
            [AnalyzerEntityType.PhoneNumber] = new PresidioTextAnonymizer { Type = AnonymizerType.Redact },
            [AnalyzerEntityType.Person] = new PresidioTextAnonymizer { Type = AnonymizerType.Replace, NewValue = "ANONYMIZED" }
        };

        // Add prompt filter to anonymize rendered prompt before sending it to LLM
        builder.Services.AddSingleton<IPromptRenderFilter>(sp => new PromptAnonymizerFilter(
            sp.GetRequiredService<ILogger>(),
            sp.GetRequiredService<PresidioTextAnalyzerService>(),
            sp.GetRequiredService<PresidioTextAnonymizerService>(),
            anonymizers));

        var kernel = builder.Build();

        var executionSettings = new OpenAIPromptExecutionSettings
        {
            ChatSystemPrompt = "If prompt does not contain 'Jane Doe' - return 'true'."
        };

        var result = await kernel.InvokePromptAsync("Hello world, my name is Jane Doe. My number is: 034453334", new(executionSettings));
        logger.LogInformation("Result: {Result}", result.ToString());

        /*
        Prompt before anonymization : Hello world, my name is Jane Doe. My number is: 034453334
        Prompt after anonymization : Hello world, my name is ANONYMIZED. My number is: 
        Result: true
         */
    }

    #region Filters

    private sealed class PromptAnalyzerFilter(
        ILogger logger,
        PresidioTextAnalyzerService analyzerService) : IPromptRenderFilter
    {
        public async Task OnPromptRenderAsync(PromptRenderContext context, Func<PromptRenderContext, Task> next)
        {
            await next(context);

            var prompt = context.RenderedPrompt!;

            logger.LogTrace("Prompt: {Prompt}", prompt);

            var analyzerResults = await analyzerService.AnalyzeAsync(new PresidioTextAnalyzerRequest { Text = prompt });

            var piiDetected = false;

            foreach (var result in analyzerResults)
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

    private sealed class PromptAnonymizerFilter(
        ILogger logger,
        PresidioTextAnalyzerService analyzerService,
        PresidioTextAnonymizerService anonymizerService,
        Dictionary<string, PresidioTextAnonymizer> anonymizers) : IPromptRenderFilter
    {
        public async Task OnPromptRenderAsync(PromptRenderContext context, Func<PromptRenderContext, Task> next)
        {
            await next(context);

            var prompt = context.RenderedPrompt!;

            logger.LogTrace("Prompt before anonymization : {Prompt}", prompt);

            var analyzerResults = await analyzerService.AnalyzeAsync(new PresidioTextAnalyzerRequest { Text = prompt });

            var anonymizerResult = await anonymizerService.AnonymizeAsync(new PresidioTextAnonymizerRequest
            {
                Text = prompt,
                AnalyzerResults = analyzerResults,
                Anonymizers = anonymizers
            });

            logger.LogTrace("Prompt after anonymization : {Prompt}", anonymizerResult.Text);

            context.RenderedPrompt = anonymizerResult.Text;
        }
    }

    #endregion

    #region Microsoft Presidio Text Analyzer

    private readonly struct AnalyzerEntityType(string name)
    {
        public string Name { get; } = name;

        public static AnalyzerEntityType Person = new("PERSON");
        public static AnalyzerEntityType PhoneNumber = new("PHONE_NUMBER");
        public static AnalyzerEntityType EmailAddress = new("EMAIL_ADDRESS");
        public static AnalyzerEntityType USDriverLicense = new("US_DRIVER_LICENSE");

        public static implicit operator string(AnalyzerEntityType type) => type.Name;
    }

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

    #region Microsoft Presidio Text Anonymizer

    private readonly struct AnonymizerType(string name)
    {
        public string Name { get; } = name;

        public static AnonymizerType Hash = new("hash");
        public static AnonymizerType Mask = new("mask");
        public static AnonymizerType Redact = new("redact");
        public static AnonymizerType Replace = new("replace");
        public static AnonymizerType Encrypt = new("encrypt");

        public static implicit operator string(AnonymizerType type) => type.Name;
    }

    private sealed class PresidioTextAnonymizer
    {
        [JsonPropertyName("type")]
        public string Type { get; set; }

        [JsonPropertyName("new_value")]
        public string NewValue { get; set; }
    }

    private sealed class PresidioTextAnonymizerRequest
    {
        /// <summary>The text to anonymize.</summary>
        [JsonPropertyName("text")]
        public string Text { get; set; }

        /// <summary>Object where the key is DEFAULT or the ENTITY_TYPE and the value is the anonymizer definition.</summary>
        [JsonPropertyName("anonymizers")]
        public Dictionary<string, PresidioTextAnonymizer> Anonymizers { get; set; }

        /// <summary>Array of analyzer detections</summary>
        [JsonPropertyName("analyzer_results")]
        public List<PresidioTextAnalyzerResponse> AnalyzerResults { get; set; }
    }

    private sealed class PresidioTextAnonymizerResponseItem
    {
        /// <summary>Name of the used operator.</summary>
        [JsonPropertyName("operator")]
        public string Operator { get; set; }

        /// <summary>Type of the PII entity.</summary>
        [JsonPropertyName("entity_type")]
        public string EntityType { get; set; }

        /// <summary>Start index of the changed text.</summary>
        [JsonPropertyName("start")]
        public int Start { get; set; }

        /// <summary>End index in the changed text.</summary>
        [JsonPropertyName("end")]
        public int End { get; set; }
    }

    private sealed class PresidioTextAnonymizerResponse
    {
        /// <summary>The new text returned.</summary>
        [JsonPropertyName("text")]
        public string Text { get; set; }

        /// <summary>Array of anonymized entities.</summary>
        [JsonPropertyName("items")]
        public List<PresidioTextAnonymizerResponseItem> Items { get; set; }
    }

    private sealed class PresidioTextAnonymizerService(HttpClient httpClient)
    {
        private const string RequestUri = "anonymize";

        public async Task<PresidioTextAnonymizerResponse> AnonymizeAsync(PresidioTextAnonymizerRequest request)
        {
            var requestContent = new StringContent(JsonSerializer.Serialize(request), Encoding.UTF8, "application/json");

            var response = await httpClient.PostAsync(new Uri(RequestUri, UriKind.Relative), requestContent);

            response.EnsureSuccessStatusCode();

            var responseContent = await response.Content.ReadAsStringAsync();

            return JsonSerializer.Deserialize<PresidioTextAnonymizerResponse>(responseContent) ??
                throw new Exception("Anonymizer response is not available.");
        }
    }

    #endregion
}
