// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.PaLM.TextCompletion;

/*
/// <summary>
/// HTTP Schema for completion response.
/// </summary>
public sealed class TextCompletionResponse
{
    /// <summary>
    /// Completed text.
    /// </summary>
    [JsonPropertyName("generated_text")]
    public string? Text { get; set; }
}*/

public class TextCompletionResponse
{
    public Candidate[] candidates { get; set; }
}

public class Candidate
{
    public string output { get; set; }
    public Safetyrating[] safetyRatings { get; set; }
}

public class Safetyrating
{
    public string category { get; set; }
    public string probability { get; set; }
}
