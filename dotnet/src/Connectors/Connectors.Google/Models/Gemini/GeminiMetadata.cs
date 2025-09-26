// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;

namespace Microsoft.SemanticKernel.Connectors.Google;

/// <summary>
/// Represents the metadata associated with a Gemini response.
/// </summary>
public sealed class GeminiMetadata : ReadOnlyDictionary<string, object?>
{
    internal GeminiMetadata() : base(new Dictionary<string, object?>()) { }

    private GeminiMetadata(IDictionary<string, object?> dictionary) : base(dictionary) { }

    /// <summary>
    /// Reason why the processing was finished.
    /// </summary>
    public GeminiFinishReason? FinishReason
    {
        get => this.GetValueFromDictionary(nameof(this.FinishReason)) as GeminiFinishReason?;
        internal init => this.SetValueInDictionary(value, nameof(this.FinishReason));
    }

    /// <summary>
    /// Index of the response.
    /// </summary>
    public int Index
    {
        get => (this.GetValueFromDictionary(nameof(this.Index)) as int?) ?? 0;
        internal init => this.SetValueInDictionary(value, nameof(this.Index));
    }

    /// <summary>
    /// The count of tokens in the prompt.
    /// </summary>
    public int PromptTokenCount
    {
        get => (this.GetValueFromDictionary(nameof(this.PromptTokenCount)) as int?) ?? 0;
        internal init => this.SetValueInDictionary(value, nameof(this.PromptTokenCount));
    }

    /// <summary>
    /// The count of token in the current candidate.
    /// </summary>
    public int CurrentCandidateTokenCount
    {
        get => (this.GetValueFromDictionary(nameof(this.CurrentCandidateTokenCount)) as int?) ?? 0;
        internal init => this.SetValueInDictionary(value, nameof(this.CurrentCandidateTokenCount));
    }

    /// <summary>
    /// The total count of tokens of the all candidate responses.
    /// </summary>
    public int CandidatesTokenCount
    {
        get => (this.GetValueFromDictionary(nameof(this.CandidatesTokenCount)) as int?) ?? 0;
        internal init => this.SetValueInDictionary(value, nameof(this.CandidatesTokenCount));
    }

    /// <summary>
    /// The total count of tokens (prompt + total candidates token count).
    /// </summary>
    public int TotalTokenCount
    {
        get => (this.GetValueFromDictionary(nameof(this.TotalTokenCount)) as int?) ?? 0;
        internal init => this.SetValueInDictionary(value, nameof(this.TotalTokenCount));
    }

    /// <summary>
    /// The reason why prompt was blocked.
    /// </summary>
    public string? PromptFeedbackBlockReason
    {
        get => this.GetValueFromDictionary(nameof(this.PromptFeedbackBlockReason)) as string;
        internal init => this.SetValueInDictionary(value, nameof(this.PromptFeedbackBlockReason));
    }

    /// <summary>
    /// List of safety ratings for the prompt feedback.
    /// </summary>
    public IReadOnlyList<GeminiSafetyRating>? PromptFeedbackSafetyRatings
    {
        get => this.GetValueFromDictionary(nameof(this.PromptFeedbackSafetyRatings)) as IReadOnlyList<GeminiSafetyRating>;
        internal init => this.SetValueInDictionary(value, nameof(this.PromptFeedbackSafetyRatings));
    }

    /// <summary>
    /// List of safety ratings for the response.
    /// </summary>
    public IReadOnlyList<GeminiSafetyRating>? ResponseSafetyRatings
    {
        get => this.GetValueFromDictionary(nameof(this.ResponseSafetyRatings)) as IReadOnlyList<GeminiSafetyRating>;
        internal init => this.SetValueInDictionary(value, nameof(this.ResponseSafetyRatings));
    }

    /// <summary>
    /// GroundingMetadata, returned when grounding enabled.
    /// </summary>
    public GeminiGroundingMetadata? GroundingMetadata
    {
        get => this.GetValueFromDictionary(nameof(this.GroundingMetadata)) as GeminiGroundingMetadata;
        internal init => this.SetValueInDictionary(value, nameof(this.GroundingMetadata));
    }

    /// <summary>
    /// Converts a dictionary to a <see cref="GeminiMetadata"/> object.
    /// </summary>
    public static GeminiMetadata FromDictionary(IReadOnlyDictionary<string, object?> dictionary) => dictionary switch
    {
        null => throw new ArgumentNullException(nameof(dictionary)),
        GeminiMetadata metadata => metadata,
        IDictionary<string, object?> metadata => new GeminiMetadata(metadata),
        _ => new GeminiMetadata(dictionary.ToDictionary(pair => pair.Key, pair => pair.Value))
    };

    private void SetValueInDictionary(object? value, string propertyName)
        => this.Dictionary[propertyName] = value;

    private object? GetValueFromDictionary(string propertyName)
        => this.Dictionary.TryGetValue(propertyName, out var value) ? value : null;
}
