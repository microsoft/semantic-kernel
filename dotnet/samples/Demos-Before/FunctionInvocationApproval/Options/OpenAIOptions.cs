// Copyright (c) Microsoft. All rights reserved.

namespace FunctionInvocationApproval.Options;

/// <summary>
/// Configuration for OpenAI chat completion service.
/// </summary>
public class OpenAIOptions
{
    public const string SectionName = "OpenAI";

    /// <summary>
    /// OpenAI model ID, see https://platform.openai.com/docs/models.
    /// </summary>
    public string ChatModelId { get; set; }

    /// <summary>
    /// OpenAI API key, see https://platform.openai.com/account/api-keys
    /// </summary>
    public string ApiKey { get; set; }

    public bool IsValid =>
        !string.IsNullOrWhiteSpace(this.ChatModelId) &&
        !string.IsNullOrWhiteSpace(this.ApiKey);
}
