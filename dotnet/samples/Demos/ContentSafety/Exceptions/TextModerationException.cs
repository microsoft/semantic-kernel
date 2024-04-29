// Copyright (c) Microsoft. All rights reserved.

using Azure.AI.ContentSafety;

namespace ContentSafety.Exceptions;

/// <summary>
/// Exception which is thrown when offensive content is detected in user prompt or documents.
/// More information here: https://learn.microsoft.com/en-us/azure/ai-services/content-safety/quickstart-text#interpret-the-api-response
/// </summary>
public class TextModerationException : Exception
{
    /// <summary>
    /// Analysis result for categories.
    /// More information here: https://learn.microsoft.com/en-us/azure/ai-services/content-safety/concepts/harm-categories
    /// </summary>
    public IReadOnlyList<TextCategoriesAnalysis> CategoriesAnalysis { get; init; }

    public TextModerationException()
    {
    }

    public TextModerationException(string? message) : base(message)
    {
    }

    public TextModerationException(string? message, Exception? innerException) : base(message, innerException)
    {
    }
}
