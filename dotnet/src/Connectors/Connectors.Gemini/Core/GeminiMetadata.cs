#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Runtime.CompilerServices;

namespace Microsoft.SemanticKernel.Connectors.Gemini.Core;

/// <summary>
/// Represents the metadata associated with a Gemini response.
/// </summary>
public sealed class GeminiMetadata : ReadOnlyDictionary<string, object?>
{
    private readonly string? _finishReason;
    private readonly int _index;
    private readonly int _promptTokenCount;
    private readonly int _currentCandidateTokenCount;
    private readonly int _candidatesTokenCount;
    private readonly int _totalTokenCount;
    private readonly string? _promptFeedbackBlockReason;
    private readonly IReadOnlyList<GeminiMetadataSafetyRating>? _promptFeedbackSafetyRatings;
    private readonly IReadOnlyList<GeminiMetadataSafetyRating>? _responseSafetyRatings;

    internal GeminiMetadata() : base(new Dictionary<string, object?>()) { }

    /// <summary>
    /// Reason why the processing was finished.
    /// </summary>
    public string? FinishReason
    {
        get => this._finishReason;
        init
        {
            this._finishReason = value;
            this.SetValueInDictionary(value);
        }
    }

    /// <summary>
    /// Index of the response.
    /// </summary>
    public int Index
    {
        get => this._index;
        init
        {
            this._index = value;
            this.SetValueInDictionary(value);
        }
    }

    /// <summary>
    /// The count of tokens in the prompt.
    /// </summary>
    public int PromptTokenCount
    {
        get => this._promptTokenCount;
        init
        {
            this._promptTokenCount = value;
            this.SetValueInDictionary(value);
        }
    }

    /// <summary>
    /// The count of token in the current candidate.
    /// </summary>
    public int CurrentCandidateTokenCount
    {
        get => this._currentCandidateTokenCount;
        init
        {
            this._currentCandidateTokenCount = value;
            this.SetValueInDictionary(value);
        }
    }

    /// <summary>
    /// The total count of tokens of the all candidate responses.
    /// </summary>
    public int CandidatesTokenCount
    {
        get => this._candidatesTokenCount;
        init
        {
            this._candidatesTokenCount = value;
            this.SetValueInDictionary(value);
        }
    }

    /// <summary>
    /// The total count of tokens (prompt + total candidates token count).
    /// </summary>
    public int TotalTokenCount
    {
        get => this._totalTokenCount;
        init
        {
            this._totalTokenCount = value;
            this.SetValueInDictionary(value);
        }
    }

    /// <summary>
    /// The reason why prompt was blocked.
    /// </summary>
    public string? PromptFeedbackBlockReason
    {
        get => this._promptFeedbackBlockReason;
        init
        {
            this._promptFeedbackBlockReason = value;
            this.SetValueInDictionary(value);
        }
    }

    /// <summary>
    /// List of safety ratings for the prompt feedback.
    /// </summary>
    public IReadOnlyList<GeminiMetadataSafetyRating>? PromptFeedbackSafetyRatings
    {
        get => this._promptFeedbackSafetyRatings;
        init
        {
            this._promptFeedbackSafetyRatings = value;
            this.SetValueInDictionary(value);
        }
    }

    /// <summary>
    /// List of safety ratings for the response.
    /// </summary>
    public IReadOnlyList<GeminiMetadataSafetyRating>? ResponseSafetyRatings
    {
        get => this._responseSafetyRatings;
        init
        {
            this._responseSafetyRatings = value;
            this.SetValueInDictionary(value);
        }
    }

    private void SetValueInDictionary(object? value, [CallerMemberName] string propertyName = "")
    {
        this.Dictionary[propertyName] = value;
    }
}

/// <summary>
/// Represents the Gemini metadata safety settings.
/// </summary>
public sealed class GeminiMetadataSafetyRating
{
    internal GeminiMetadataSafetyRating() { }

    /// <summary>
    /// Indicates whether the response is blocked.
    /// </summary>
    public bool Block { get; init; }

    /// <summary>
    /// The category associated with the safety settings.
    /// </summary>
    public GeminiSafetyCategory? Category { get; init; }

    /// <summary>
    /// Probability score associated with the safety settings.
    /// </summary>
    public GeminiSafetyProbability? Probability { get; init; }
}
