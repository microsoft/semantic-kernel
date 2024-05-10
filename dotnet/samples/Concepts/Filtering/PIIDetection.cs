// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;

namespace Filtering;

/// <summary>
/// This example shows how to implement Personal Identifiable Information (PII) detection with Filters using Microsoft Presidio service: https://github.com/microsoft/presidio.
/// How to run Presidio on Docker locally: https://microsoft.github.io/presidio/installation/#using-docker.
/// </summary>
public class PIIDetection(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Use Presidio Text Analyzer to detect PII information in prompt with specified score threshold.
    /// If the score exceeds the threshold, prompt won't be sent to LLM and custom result will be returned from function.
    /// Text Analyzer API: https://microsoft.github.io/presidio/api-docs/api-docs.html#tag/Analyzer.
    /// </summary>
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
        var logger = this.LoggerFactory.CreateLogger<PIIDetection>();
        builder.Services.AddSingleton<ILogger>(logger);

        // Add Microsoft Presidio Text Analyzer service and configure HTTP client for it
        builder.Services.AddHttpClient<PresidioTextAnalyzerService>(client => { client.BaseAddress = new Uri("http://localhost:5001"); });

        // Add prompt filter to analyze rendered prompt for PII before sending it to LLM.
        // It's possible to change confidence score threshold value from 0 to 1 during testing to see how the logic will behave.
        builder.Services.AddSingleton<IPromptRenderFilter>(sp => new PromptAnalyzerFilter(
            sp.GetRequiredService<ILogger>(),
            sp.GetRequiredService<PresidioTextAnalyzerService>(),
            scoreThreshold: 0.9));

        var kernel = builder.Build();

        // Example 1: Use prompt with PII
        try
        {
            await kernel.InvokePromptAsync("John Smith has a card 1111 2222 3333 4444");
        }
        catch (KernelException exception)
        {
            logger.LogError("Exception: {Exception}", exception.Message);
        }

        /* 
        Prompt: John Smith has a card 1111 2222 3333 4444
        Entity type: CREDIT_CARD. Score: 1
        Entity type: PERSON. Score: 0.85
        Exception: Prompt contains PII information. Operation is canceled.
        */

        // Example 2: Use prompt without PII
        var result = await kernel.InvokePromptAsync("Hi, can you help me?");
        logger.LogInformation("Result: {Result}", result.ToString());

        /*
        Prompt: Hi, can you help me?
        Result: Of course! I'm here to help. What do you need assistance with?
        */
    }

    /// <summary>
    /// Use Presidio Text Anonymizer to detect PII information in prompt and update the prompt by following specified rules before sending it to LLM.
    /// Text Anonymizer API: https://microsoft.github.io/presidio/api-docs/api-docs.html#tag/Anonymizer.
    /// </summary>
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
        var logger = this.LoggerFactory.CreateLogger<PIIDetection>();
        builder.Services.AddSingleton<ILogger>(logger);

        // Add Microsoft Presidio Text Analyzer service and configure HTTP client for it. Text Analyzer results are required for Text Anonymizer input.
        builder.Services.AddHttpClient<PresidioTextAnalyzerService>(client => { client.BaseAddress = new Uri("http://localhost:5001"); });

        // Add Microsoft Presidio Text Anonymizer service and configure HTTP client for it
        builder.Services.AddHttpClient<PresidioTextAnonymizerService>(client => { client.BaseAddress = new Uri("http://localhost:5002"); });

        // Define anonymizer rules: redact phone number and replace person name with word "ANONYMIZED"
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

        builder.Plugins.AddFromType<SearchPlugin>();

        var kernel = builder.Build();

        // Define instructions for LLM how to react when certain conditions are met for demonstration purposes
        var executionSettings = new OpenAIPromptExecutionSettings
        {
            ChatSystemPrompt = "If prompt does not contain first and last names - return 'true'."
        };

        // Define function with Handlebars prompt template, using markdown table for data representation.
        // Data is fetched using SearchPlugin.GetContacts function.
        var function = kernel.CreateFunctionFromPrompt(
            new()
            {
                Template =
                """
                | Name | Phone number | Position |
                |------|--------------|----------|
                {{#each (SearchPlugin-GetContacts)}}
                | {{Name}} | {{Phone}} | {{Position}} |
                {{/each}}
                """,
                TemplateFormat = "handlebars"
            },
            new HandlebarsPromptTemplateFactory()
        );

        var result = await kernel.InvokeAsync(function, new(executionSettings));
        logger.LogInformation("Result: {Result}", result.ToString());

        /*
        Prompt before anonymization : 
        | Name        | Phone number      | Position  |
        |-------------|-------------------|---------- |
        | John Smith  | +1 (123) 456-7890 | Developer |
        | Alice Doe   | +1 (987) 654-3120 | Manager   |
        | Emily Davis | +1 (555) 555-5555 | Designer  |

        Prompt after anonymization : 
        | Name        | Phone number      | Position  |
        |-------------|-------------------|-----------|
        | ANONYMIZED  | +1                | Developer |
        | ANONYMIZED  | +1                | Manager   |
        | ANONYMIZED  | +1                | Designer  |

        Result: true
        */
    }

    #region Filters

    /// <summary>
    /// Filter which use Text Analyzer to detect PII in prompt and prevent sending it to LLM.
    /// </summary>
    private sealed class PromptAnalyzerFilter(
        ILogger logger,
        PresidioTextAnalyzerService analyzerService,
        double scoreThreshold) : IPromptRenderFilter
    {
        public async Task OnPromptRenderAsync(PromptRenderContext context, Func<PromptRenderContext, Task> next)
        {
            await next(context);

            // Get rendered prompt
            var prompt = context.RenderedPrompt!;

            logger.LogTrace("Prompt: {Prompt}", prompt);

            // Call analyzer to detect PII
            var analyzerResults = await analyzerService.AnalyzeAsync(new PresidioTextAnalyzerRequest { Text = prompt });

            var piiDetected = false;

            // Check analyzer results
            foreach (var result in analyzerResults)
            {
                logger.LogInformation("Entity type: {EntityType}. Score: {Score}", result.EntityType, result.Score);

                if (result.Score > scoreThreshold)
                {
                    piiDetected = true;
                }
            }

            // If PII detected, throw an exception to prevent this prompt from being sent to LLM.
            // It's also possible to override 'context.Result' to return some default function result instead.
            if (piiDetected)
            {
                throw new KernelException("Prompt contains PII information. Operation is canceled.");
            }
        }
    }

    /// <summary>
    /// Filter which use Text Anonymizer to detect PII in prompt and update the prompt by following specified rules before sending it to LLM.
    /// </summary>
    private sealed class PromptAnonymizerFilter(
        ILogger logger,
        PresidioTextAnalyzerService analyzerService,
        PresidioTextAnonymizerService anonymizerService,
        Dictionary<string, PresidioTextAnonymizer> anonymizers) : IPromptRenderFilter
    {
        public async Task OnPromptRenderAsync(PromptRenderContext context, Func<PromptRenderContext, Task> next)
        {
            await next(context);

            // Get rendered prompt
            var prompt = context.RenderedPrompt!;

            logger.LogTrace("Prompt before anonymization : \n{Prompt}", prompt);

            // Call analyzer to detect PII
            var analyzerResults = await analyzerService.AnalyzeAsync(new PresidioTextAnalyzerRequest { Text = prompt });

            // Call anonymizer to update the prompt by following specified rules. Pass analyzer results received on previous step.
            var anonymizerResult = await anonymizerService.AnonymizeAsync(new PresidioTextAnonymizerRequest
            {
                Text = prompt,
                AnalyzerResults = analyzerResults,
                Anonymizers = anonymizers
            });

            logger.LogTrace("Prompt after anonymization : \n{Prompt}", anonymizerResult.Text);

            // Update prompt in context to sent new prompt without PII to LLM
            context.RenderedPrompt = anonymizerResult.Text;
        }
    }

    #endregion

    #region Microsoft Presidio Text Analyzer

    /// <summary>
    /// PII entities Presidio Text Analyzer is capable of detecting. Only some of them are defined here for demonstration purposes.
    /// Full list can be found here: https://microsoft.github.io/presidio/api-docs/api-docs.html#tag/Analyzer/paths/~1supportedentities/get.
    /// </summary>
    private readonly struct AnalyzerEntityType(string name)
    {
        public string Name { get; } = name;

        public static AnalyzerEntityType Person = new("PERSON");
        public static AnalyzerEntityType PhoneNumber = new("PHONE_NUMBER");
        public static AnalyzerEntityType EmailAddress = new("EMAIL_ADDRESS");
        public static AnalyzerEntityType CreditCard = new("CREDIT_CARD");

        public static implicit operator string(AnalyzerEntityType type) => type.Name;
    }

    /// <summary>
    /// Request model for Text Analyzer. Only required properties are defined here for demonstration purposes.
    /// Full schema can be found here: https://microsoft.github.io/presidio/api-docs/api-docs.html#tag/Analyzer/paths/~1analyze/post.
    /// </summary>
    private sealed class PresidioTextAnalyzerRequest
    {
        /// <summary>The text to analyze.</summary>
        [JsonPropertyName("text")]
        public string Text { get; set; }

        /// <summary>Two characters for the desired language in ISO_639-1 format.</summary>
        [JsonPropertyName("language")]
        public string Language { get; set; } = "en";
    }

    /// <summary>
    /// Response model from Text Analyzer. Only required properties are defined here for demonstration purposes.
    /// Full schema can be found here: https://microsoft.github.io/presidio/api-docs/api-docs.html#tag/Analyzer/paths/~1analyze/post.
    /// </summary>
    private sealed class PresidioTextAnalyzerResponse
    {
        /// <summary>Where the PII starts.</summary>
        [JsonPropertyName("start")]
        public int Start { get; set; }

        /// <summary>Where the PII ends.</summary>
        [JsonPropertyName("end")]
        public int End { get; set; }

        /// <summary>The PII detection confidence score from 0 to 1.</summary>
        [JsonPropertyName("score")]
        public double Score { get; set; }

        /// <summary>The supported PII entity types.</summary>
        [JsonPropertyName("entity_type")]
        public string EntityType { get; set; }
    }

    /// <summary>
    /// Service which performs HTTP request to Text Analyzer.
    /// </summary>
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

    /// <summary>
    /// Anonymizer action type that can be performed to update the prompt.
    /// More information here: https://microsoft.github.io/presidio/api-docs/api-docs.html#tag/Anonymizer/paths/~1anonymizers/get
    /// </summary>
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

    /// <summary>
    /// Anonymizer model that describes how to update the prompt.
    /// </summary>
    private sealed class PresidioTextAnonymizer
    {
        /// <summary>Anonymizer action type that can be performed to update the prompt.</summary>
        [JsonPropertyName("type")]
        public string Type { get; set; }

        /// <summary>New value for "replace" anonymizer type.</summary>
        [JsonPropertyName("new_value")]
        public string NewValue { get; set; }
    }

    /// <summary>
    /// Request model for Text Anonymizer.
    /// Full schema can be found here: https://microsoft.github.io/presidio/api-docs/api-docs.html#tag/Anonymizer/paths/~1anonymize/post
    /// </summary>
    private sealed class PresidioTextAnonymizerRequest
    {
        /// <summary>The text to anonymize.</summary>
        [JsonPropertyName("text")]
        public string Text { get; set; }

        /// <summary>Object where the key is DEFAULT or the ENTITY_TYPE and the value is the anonymizer definition.</summary>
        [JsonPropertyName("anonymizers")]
        public Dictionary<string, PresidioTextAnonymizer> Anonymizers { get; set; }

        /// <summary>Array of analyzer detections.</summary>
        [JsonPropertyName("analyzer_results")]
        public List<PresidioTextAnalyzerResponse> AnalyzerResults { get; set; }
    }

    /// <summary>
    /// Response item model for Text Anonymizer.
    /// Full schema can be found here: https://microsoft.github.io/presidio/api-docs/api-docs.html#tag/Anonymizer/paths/~1anonymize/post
    /// </summary>
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

    /// <summary>
    /// Response model for Text Anonymizer.
    /// Full schema can be found here: https://microsoft.github.io/presidio/api-docs/api-docs.html#tag/Anonymizer/paths/~1anonymize/post
    /// </summary>
    private sealed class PresidioTextAnonymizerResponse
    {
        /// <summary>The new text returned.</summary>
        [JsonPropertyName("text")]
        public string Text { get; set; }

        /// <summary>Array of anonymized entities.</summary>
        [JsonPropertyName("items")]
        public List<PresidioTextAnonymizerResponseItem> Items { get; set; }
    }

    /// <summary>
    /// Service which performs HTTP request to Text Anonymizer.
    /// </summary>
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

    #region Plugins

    /// <summary>
    /// Contact model for demonstration purposes.
    /// </summary>
    private sealed class Contact
    {
        public string Name { get; set; }
        public string Phone { get; set; }
        public string Position { get; set; }
    }

    /// <summary>
    /// Search Plugin to be called from prompt for demonstration purposes.
    /// </summary>
    private sealed class SearchPlugin
    {
        [KernelFunction]
        public List<Contact> GetContacts() => new()
            {
                new () { Name = "John Smith", Phone = "+1 (123) 456-7890", Position = "Developer" },
                new () { Name = "Alice Doe", Phone = "+1 (987) 654-3120", Position = "Manager" },
                new () { Name = "Emily Davis", Phone = "+1 (555) 555-5555", Position = "Designer" }
            };
    }

    #endregion
}
