// Copyright (c) Microsoft. All rights reserved.

namespace ProcessFramework.Aspire.Shared;

/// <summary>
/// Represents a request to summarize a given text.
/// </summary>
public class SummarizeRequest
{
    /// <summary>
    /// Gets or sets the text to be summarized.
    /// </summary>
    public string TextToSummarize { get; set; } = string.Empty;
}
