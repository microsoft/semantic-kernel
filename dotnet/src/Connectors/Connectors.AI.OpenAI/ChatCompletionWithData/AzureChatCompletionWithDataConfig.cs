// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletionWithData;

/// <summary>
/// Required configuration for Azure OpenAI chat completion with data.
/// More information: <see href="https://learn.microsoft.com/en-us/azure/ai-services/openai/use-your-data-quickstart"/>
/// </summary>
public class AzureChatCompletionWithDataConfig
{
    /// <summary>
    /// Azure OpenAI model ID or deployment name, see <see href="https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource"/>
    /// </summary>
    public string CompletionModelId { get; set; } = string.Empty;

    /// <summary>
    /// Azure OpenAI deployment URL, see <see href="https://learn.microsoft.com/azure/cognitive-services/openai/quickstart"/>
    /// </summary>
    public string CompletionEndpoint { get; set; } = string.Empty;

    /// <summary>
    /// Azure OpenAI API key, see <see href="https://learn.microsoft.com/azure/cognitive-services/openai/quickstart"/>
    /// </summary>
    public string CompletionApiKey { get; set; } = string.Empty;

    /// <summary>
    /// Azure OpenAI Completion API version (e.g. 2023-06-01-preview)
    /// </summary>
    public string CompletionApiVersion { get; set; } = string.Empty;

    /// <summary>
    /// Data source endpoint URL.
    /// For Azure Cognitive Search, see <see href="https://learn.microsoft.com/en-us/azure/search/search-create-service-portal"/>
    /// </summary>
    public string DataSourceEndpoint { get; set; } = string.Empty;

    /// <summary>
    /// Data source API key.
    /// For Azure Cognitive Search keys, see <see href="https://learn.microsoft.com/en-us/azure/search/search-security-api-keys#find-existing-keys"/>
    /// </summary>
    public string DataSourceApiKey { get; set; } = string.Empty;

    /// <summary>
    /// Data source index name.
    /// For Azure Cognitive Search indexes, see <see href="https://learn.microsoft.com/en-us/azure/search/search-how-to-create-search-index"/>
    /// </summary>
    public string DataSourceIndex { get; set; } = string.Empty;

    /// <summary>
    /// Responsible AI Policy. For example policy is '146' used for Text Harmful, Hate, Sexual content and Jailbreak
    /// </summary>
    public string ResponsibleAIPolicy { get; set; } = string.Empty;
}
