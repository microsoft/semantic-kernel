// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;

namespace Microsoft.SemanticKernel.Connectors.HuggingFace;

/// <summary>
/// Represents the metadata of a Hugging Face chat completion.
/// </summary>
public sealed class HuggingFaceChatCompletionMetadata : ReadOnlyDictionary<string, object?>
{
    internal HuggingFaceChatCompletionMetadata() : base(new Dictionary<string, object?>()) { }

    private HuggingFaceChatCompletionMetadata(IDictionary<string, object?> dictionary) : base(dictionary) { }

    /// <summary>
    /// Object identifier.
    /// </summary>
#pragma warning disable CA1720 // Identifier contains type name
    public string? Object
    {
        get => this.GetValueFromDictionary(nameof(this.Object)) as string;
        internal init => this.SetValueInDictionary(value, nameof(this.Object));
    }
#pragma warning restore CA1720 // Identifier contains type name

    /// <summary>
    /// Creation time of the response.
    /// </summary>
    public long? Created
    {
        get => (this.GetValueFromDictionary(nameof(this.Created)) as long?) ?? 0;
        internal init => this.SetValueInDictionary(value, nameof(this.Created));
    }

    /// <summary>
    /// Model used to generate the response.
    /// </summary>
    public string? Model
    {
        get => this.GetValueFromDictionary(nameof(this.Model)) as string;
        internal init => this.SetValueInDictionary(value, nameof(this.Model));
    }

    /// <summary>
    /// Reason why the processing was finished.
    /// </summary>
    public string? FinishReason
    {
        get => this.GetValueFromDictionary(nameof(this.FinishReason)) as string;
        internal init => this.SetValueInDictionary(value, nameof(this.FinishReason));
    }

    /// <summary>
    /// System fingerprint.
    /// </summary>
    public string? SystemFingerPrint
    {
        get => this.GetValueFromDictionary(nameof(this.SystemFingerPrint)) as string;
        internal init => this.SetValueInDictionary(value, nameof(this.SystemFingerPrint));
    }

    /// <summary>
    /// Id of the response.
    /// </summary>
    public string? Id
    {
        get => this.GetValueFromDictionary(nameof(this.Id)) as string;
        internal init => this.SetValueInDictionary(value, nameof(this.Id));
    }

    /// <summary>
    /// The total count of tokens used.
    /// </summary>
    /// <remarks>
    /// Usage is not available for streaming chunks.
    /// </remarks>
    public int? UsageTotalTokens
    {
        get => (this.GetValueFromDictionary(nameof(this.UsageTotalTokens)) as int?);
        internal init => this.SetValueInDictionary(value, nameof(this.UsageTotalTokens));
    }

    /// <summary>
    /// The count of tokens in the prompt.
    /// </summary>
    /// <remarks>
    /// Usage is not available for streaming chunks.
    /// </remarks>
    public int? UsagePromptTokens
    {
        get => (this.GetValueFromDictionary(nameof(this.UsagePromptTokens)) as int?);
        internal init => this.SetValueInDictionary(value, nameof(this.UsagePromptTokens));
    }

    /// <summary>
    /// The count of token in the current completion.
    /// </summary>
    /// <remarks>
    /// Usage is not available for streaming chunks.
    /// </remarks>
    public int? UsageCompletionTokens
    {
        get => (this.GetValueFromDictionary(nameof(this.UsageCompletionTokens)) as int?);
        internal init => this.SetValueInDictionary(value, nameof(this.UsageCompletionTokens));
    }

    /// <summary>
    /// The log probabilities of the completion.
    /// </summary>
    public object? LogProbs
    {
        get => this.GetValueFromDictionary(nameof(this.LogProbs));
        internal init => this.SetValueInDictionary(value, nameof(this.LogProbs));
    }

    /// <summary>
    /// Converts a dictionary to a <see cref="HuggingFaceChatCompletionMetadata"/> object.
    /// </summary>
    public static HuggingFaceChatCompletionMetadata FromDictionary(IReadOnlyDictionary<string, object?> dictionary) => dictionary switch
    {
        null => throw new ArgumentNullException(nameof(dictionary)),
        HuggingFaceChatCompletionMetadata metadata => metadata,
        IDictionary<string, object?> metadata => new HuggingFaceChatCompletionMetadata(metadata),
        _ => new HuggingFaceChatCompletionMetadata(dictionary.ToDictionary(pair => pair.Key, pair => pair.Value))
    };

    private void SetValueInDictionary(object? value, string propertyName)
        => this.Dictionary[propertyName] = value;

    private object? GetValueFromDictionary(string propertyName)
        => this.Dictionary.TryGetValue(propertyName, out var value) ? value : null;
}
