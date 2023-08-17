// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletionWithData;

public class AzureChatCompletionWithDataConfig
{
    public string CompletionModelId { get; set; } = string.Empty;

    public string CompletionEndpoint { get; set; } = string.Empty;

    public string CompletionApiKey { get; set; } = string.Empty;

    public string CompletionApiVersion { get; set; } = string.Empty;

    public string DataSourceEndpoint { get; set; } = string.Empty;

    public string DataSourceApiKey { get; set; } = string.Empty;

    public string DataSourceIndex { get; set; } = string.Empty;
}
