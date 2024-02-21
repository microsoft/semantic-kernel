// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Runtime.CompilerServices;

namespace Microsoft.SemanticKernel.Connectors.HuggingFace.Core;

/// <summary>
/// Represents the metadata of the Ollama response.
/// </summary>
public sealed class HuggingFaceStreamMetadata : ReadOnlyDictionary<string, object?>
{
    internal HuggingFaceStreamMetadata(TextGenerationStreamResponse response) : base(new Dictionary<string, object?>())
    {
        this.Details = response.Details;
        this.Index = response.Index;
        this.GeneratedText = response.GeneratedText;
        this.TokenId = response.Token.Id;
        this.TokenLogProb = response.Token.LogProb;
        this.TokenSpecial = response.Token.Special;
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
    public int Index
    {
        get => (this.GetValueFromDictionary() as int?) ?? 0;
        internal init => this.SetValueInDictionary(value);
    }

    /// <summary>
    /// Unique token idenfitier for the model
    /// </summary>
    public int TokenId
    {
        get => (this.GetValueFromDictionary() as int?) ?? 0;
        internal init => this.SetValueInDictionary(value);
    }

    private void SetValueInDictionary(object? value, [CallerMemberName] string propertyName = "")
        => this.Dictionary[propertyName] = value;

    private object? GetValueFromDictionary([CallerMemberName] string propertyName = "")
        => this.Dictionary.TryGetValue(propertyName, out var value) ? value : null;
}
