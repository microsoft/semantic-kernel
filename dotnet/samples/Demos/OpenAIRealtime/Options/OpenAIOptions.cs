// Copyright (c) Microsoft. All rights reserved.

namespace OpenAIRealtime;

/// <summary>
/// Configuration for OpenAI service.
/// </summary>
public class OpenAIOptions
{
    public const string SectionName = "OpenAI";

    /// <summary>
    /// OpenAI API key, see https://platform.openai.com/account/api-keys
    /// </summary>
    public string ApiKey { get; set; }

    public bool IsValid =>
        !string.IsNullOrWhiteSpace(this.ApiKey);
}
