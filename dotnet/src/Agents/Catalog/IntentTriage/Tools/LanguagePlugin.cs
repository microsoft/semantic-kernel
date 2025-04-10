// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.IO;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Net.Mime;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.IntentTriage.Logging;

namespace Microsoft.SemanticKernel.Agents.IntentTriage;

internal sealed class LanguagePlugin
{
    private const string EndpointCLU = "language/:analyze-conversations";
    private const string EndpointCQA = "language/:query-knowledgebases";
    public const string HeaderSubscriptionKey = "ocp-apim-subscription-key";

    private readonly IntentTriageLanguageSettings _settings;

    public LanguagePlugin(IntentTriageLanguageSettings settings)
    {
        this._settings = settings;
    }

    [KernelFunction, Description("Detects the intent of the message")]
    public async Task<QualifiedResult?> AnalyzeMessageAsync(string message, ILogger logger)
    {
        Uri uriEndpoint = new(this._settings.ApiEndpoint);
        Uri uriOperation = new(uriEndpoint, $"{EndpointCLU}?api-version={this._settings.ApiVersion}");

        string requestBody =
            $$$"""
            {
                "analysisInput": {
                    "conversationItem": {
                        "id": "id__001",
                        "text": {{{JsonSerializer.Serialize(message)}}},
                        "participantId": "id__001"
                    }
                },
                "parameters": {
                    "projectName": "{{{this._settings.AnalyzeProject}}}",
                    "deploymentName": "{{{this._settings.AnalyzeDeployment}}}"
                },
                "kind": "Conversation"
            }
            """;
        using StringContent request = new(requestBody, new MediaTypeHeaderValue(MediaTypeNames.Application.Json));

        logger.LogAnalyzeInvoking(uriOperation);
        JsonDocument response = await this.InvokeAPIAsync(uriOperation, request);

        // Parsing JSON in place of defining a complex object model.
        JsonElement? intents = response.RootElement.GetProperty("result", "prediction", "intents");
        JsonElement? topIntent = intents.GetFirstArrayElement();
        string? intentCategory = topIntent.GetStringValue("category");
        decimal intentConfidence = topIntent.GetDecimalValue("confidenceScore") ?? 0;
        logger.LogAnalyzeInvoked(intentCategory, intentConfidence);
        if (!string.IsNullOrWhiteSpace(intentCategory) &&
            intentConfidence >= this._settings.AnalyzeThreshold)
        {
            return
                new QualifiedResult
                {
                    Answer = $"Detected Intent: {intentCategory}",
                    Confidence = intentConfidence,
                };
        }

        return null;
    }

    [KernelFunction, Description("Provides a knowledgebase answer to the message")]
    public async Task<QualifiedResult?> QueryKnowledgeBaseAsync(string message, ILogger logger)
    {
        Uri uriEndpoint = new(this._settings.ApiEndpoint);
        Uri uriOperation =
            new(uriEndpoint,
                $"{EndpointCQA}?projectName={this._settings.QueryProject}&deploymentName={this._settings.QueryDeployment}&api-version={this._settings.ApiVersion}");

        string requestBody =
            $$$"""
            {
                "question": {{{JsonSerializer.Serialize(message)}}}
            }
            """;
        using StringContent request = new(requestBody, new MediaTypeHeaderValue(MediaTypeNames.Application.Json));

        logger.LogAnalyzeInvoking(uriOperation);
        JsonDocument response = await this.InvokeAPIAsync(uriOperation, request);

        // Parsing JSON in place of defining a complex object model.
        JsonElement? intents = response.RootElement.GetProperty(["answers"]);
        JsonElement? topIntent = intents.GetFirstArrayElement();
        string? queryResult = topIntent.GetStringValue("answer");
        decimal queryConfidence = topIntent.GetDecimalValue("confidenceScore") ?? 0;
        logger.LogAnalyzeInvoked(queryResult, queryConfidence);
        if (!string.IsNullOrWhiteSpace(queryResult) &&
            queryConfidence >= this._settings.QueryThreshold)
        {
            return
                new QualifiedResult
                {
                    Answer = queryResult,
                    Confidence = queryConfidence,
                };
        }

        return null;
    }

    // NOTE: No retry, failure detection, or resiliency measures.
    private async Task<JsonDocument> InvokeAPIAsync(Uri endpoint, HttpContent request)
    {
        using HttpClient client = new();
        client.DefaultRequestHeaders.Add(HeaderSubscriptionKey, this._settings.ApiKey);

        HttpResponseMessage response = await client.PostAsync(endpoint, request);

        string responseText = await response.Content.ReadAsStringAsync();
        await using Stream responseStream = await response.Content.ReadAsStreamAsync();
        JsonDocument responseJson = await JsonDocument.ParseAsync(responseStream);

        return responseJson;
    }
}
