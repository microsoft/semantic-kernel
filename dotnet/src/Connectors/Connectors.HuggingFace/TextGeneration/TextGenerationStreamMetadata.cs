// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Runtime.CompilerServices;
using Microsoft.SemanticKernel.Connectors.HuggingFace.Client;

namespace Microsoft.SemanticKernel.Connectors.HuggingFace.TextGeneration;

/// <summary>
/// Represents the metadata of the HuggingFace response.
/// </summary>
public sealed class TextGenerationStreamMetadata : ReadOnlyDictionary<string, object?>
{
    internal TextGenerationStreamMetadata(TextGenerationStreamResponse response) : base(new Dictionary<string, object?>())
    {
        this.Details = response.Details;
        this.Index = response.Index;
        this.GeneratedText = response.GeneratedText;
        this.TokenId = response.Token?.Id;
        this.TokenLogProb = response.Token?.LogProb;
        this.TokenSpecial = response.Token?.Special;
    }

    /// <summary>
    /// The generated text.
    /// This will only be populated in the last chunk of the response.
    /// </summary>
    public string? GeneratedText
    {
        get => this.GetValueFromDictionary() as string;
        internal init => this.SetValueInDictionary(value);
    }

    /// <summary>
    /// Detail of the current chunk of the response
    /// </summary>
    public string? Details
    {
        get => this.GetValueFromDictionary() as string;
        internal init => this.SetValueInDictionary(value);
    }

    /// <summary>
    /// Current token index of the response
    /// </summary>
    public int? Index
    {
        get => this.GetValueFromDictionary() as int?;
        internal init => this.SetValueInDictionary(value);
    }

    /// <summary>
    /// Unique token identifier for the model
    /// </summary>
    public int? TokenId
    {
        get => this.GetValueFromDictionary() as int?;
        internal init => this.SetValueInDictionary(value);
    }

    /// <summary>
    /// Gets or sets the logarithm of the probability of a specific token given its context.
    /// </summary>
    public double? TokenLogProb
    {
        get => this.GetValueFromDictionary() as double?;
        internal init => this.SetValueInDictionary(value);
    }

    /// <summary>
    /// Gets true value indicating whether the token is a special token (e.g., [CLS], [SEP], [PAD]) used for specific model purposes.
    /// </summary>
    public bool? TokenSpecial
    {
        get => this.GetValueFromDictionary() as bool?;
        internal init => this.SetValueInDictionary(value);
    }

    private void SetValueInDictionary(object? value, [CallerMemberName] string propertyName = "")
        => this.Dictionary[propertyName] = value;

    private object? GetValueFromDictionary([CallerMemberName] string propertyName = "")
        => this.Dictionary.TryGetValue(propertyName, out var value) ? value : null;
}
