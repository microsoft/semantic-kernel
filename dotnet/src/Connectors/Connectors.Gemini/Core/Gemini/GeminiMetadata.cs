#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Runtime.CompilerServices;

namespace Microsoft.SemanticKernel.Connectors.Gemini.Core.Gemini;

/// <summary>
/// Represents the metadata associated with a Gemini response.
/// </summary>
public sealed class GeminiMetadata : ReadOnlyDictionary<string, object?>
{
    internal GeminiMetadata() : base(new Dictionary<string, object?>()) { }

    /// <summary>
    /// Reason why the processing was finished.
    /// </summary>
    public GeminiFinishReason? FinishReason
    {
        get => this.GetValueFromDictionary() as GeminiFinishReason?;
        internal init => this.SetValueInDictionary(value);
    }

    /// <summary>
    /// Index of the response.
    /// </summary>
    public int Index
    {
        get => (this.GetValueFromDictionary() as int?) ?? 0;
        internal init => this.SetValueInDictionary(value);
    }

    /// <summary>
    /// The count of tokens in the prompt.
    /// </summary>
    public int PromptTokenCount
    {
        get => (this.GetValueFromDictionary() as int?) ?? 0;
        internal init => this.SetValueInDictionary(value);
    }

    /// <summary>
    /// The count of token in the current candidate.
    /// </summary>
    public int CurrentCandidateTokenCount
    {
        get => (this.GetValueFromDictionary() as int?) ?? 0;
        internal init => this.SetValueInDictionary(value);
    }

    /// <summary>
    /// The total count of tokens of the all candidate responses.
    /// </summary>
    public int CandidatesTokenCount
    {
        get => (this.GetValueFromDictionary() as int?) ?? 0;
        internal init => this.SetValueInDictionary(value);
    }

    /// <summary>
    /// The total count of tokens (prompt + total candidates token count).
    /// </summary>
    public int TotalTokenCount
    {
        get => (this.GetValueFromDictionary() as int?) ?? 0;
        internal init => this.SetValueInDictionary(value);
    }

    /// <summary>
    /// The reason why prompt was blocked.
    /// </summary>
    public string? PromptFeedbackBlockReason
    {
        get => this.GetValueFromDictionary() as string;
        internal init => this.SetValueInDictionary(value);
    }

    /// <summary>
    /// List of safety ratings for the prompt feedback.
    /// </summary>
    public IReadOnlyList<GeminiSafetyRating>? PromptFeedbackSafetyRatings
    {
        get => this.GetValueFromDictionary() as IReadOnlyList<GeminiSafetyRating>;
        internal init => this.SetValueInDictionary(value);
    }

    /// <summary>
    /// List of safety ratings for the response.
    /// </summary>
    public IReadOnlyList<GeminiSafetyRating>? ResponseSafetyRatings
    {
        get => this.GetValueFromDictionary() as IReadOnlyList<GeminiSafetyRating>;
        internal init => this.SetValueInDictionary(value);
    }

    private void SetValueInDictionary(object? value, [CallerMemberName] string propertyName = "")
        => this.Dictionary[propertyName] = value;

    private object? GetValueFromDictionary([CallerMemberName] string propertyName = "")
        => this.Dictionary.TryGetValue(propertyName, out var value) ? value : null;
}
