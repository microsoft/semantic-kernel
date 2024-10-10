// Copyright (c) Microsoft. All rights reserved.

using System.Collections;
using ContentSafety.Services.PromptShield;

namespace ContentSafety.Exceptions;

/// <summary>
/// Exception which is thrown when attack is detected in user prompt or documents.
/// More information here: https://learn.microsoft.com/en-us/azure/ai-services/content-safety/quickstart-jailbreak#interpret-the-api-response
/// </summary>
public class AttackDetectionException : Exception
{
    /// <summary>
    /// Contains analysis result for the user prompt.
    /// </summary>
    public PromptShieldAnalysis? UserPromptAnalysis { get; init; }

    /// <summary>
    /// Contains a list of analysis results for each document provided.
    /// </summary>
    public IReadOnlyList<PromptShieldAnalysis>? DocumentsAnalysis { get; init; }

    /// <summary>
    /// Dictionary with additional details of exception.
    /// </summary>
    public override IDictionary Data => new Dictionary<string, object?>()
    {
        ["userPrompt"] = this.UserPromptAnalysis,
        ["documents"] = this.DocumentsAnalysis,
    };

    public AttackDetectionException()
    {
    }

    public AttackDetectionException(string? message) : base(message)
    {
    }

    public AttackDetectionException(string? message, Exception? innerException) : base(message, innerException)
    {
    }
}
