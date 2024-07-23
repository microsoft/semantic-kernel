// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;

namespace Microsoft.SemanticKernel.Connectors.Anthropic;

/// <summary>
/// Represents the metadata associated with a Anthropic response.
/// </summary>
public sealed class AnthropicMetadata : ReadOnlyDictionary<string, object?>
{
    internal AnthropicMetadata() : base(new Dictionary<string, object?>()) { }

    private AnthropicMetadata(IDictionary<string, object?> dictionary) : base(dictionary) { }

    /// <summary>
    /// Unique message object identifier.
    /// </summary>
    public string MessageId
    {
        get => this.GetValueFromDictionary(nameof(this.MessageId)) as string ?? string.Empty;
        internal init => this.SetValueInDictionary(value, nameof(this.MessageId));
    }

    /// <summary>
    /// The reason generating was stopped.
    /// </summary>
    public AnthropicFinishReason? FinishReason
    {
        get => (AnthropicFinishReason?)this.GetValueFromDictionary(nameof(this.FinishReason));
        internal init => this.SetValueInDictionary(value, nameof(this.FinishReason));
    }

    /// <summary>
    /// Which custom stop sequence was generated, if any.
    /// </summary>
    public string? StopSequence
    {
        get => this.GetValueFromDictionary(nameof(this.StopSequence)) as string;
        internal init => this.SetValueInDictionary(value, nameof(this.StopSequence));
    }

    /// <summary>
    /// The number of input tokens which were used.
    /// </summary>
    public int? InputTokenCount
    {
        get => this.GetValueFromDictionary(nameof(this.InputTokenCount)) as int?;
        internal init => this.SetValueInDictionary(value, nameof(this.InputTokenCount));
    }

    /// <summary>
    /// The number of output tokens which were used.
    /// </summary>
    public int? OutputTokenCount
    {
        get => this.GetValueFromDictionary(nameof(this.OutputTokenCount)) as int?;
        internal init => this.SetValueInDictionary(value, nameof(this.OutputTokenCount));
    }

    /// <summary>
    /// Represents the total count of tokens in the Anthropic response,
    /// which is calculated by summing the input token count and the output token count.
    /// </summary>
    public int? TotalTokenCount => this.InputTokenCount + this.OutputTokenCount;

    /// <summary>
    /// Converts a dictionary to a <see cref="AnthropicMetadata"/> object.
    /// </summary>
    public static AnthropicMetadata FromDictionary(IReadOnlyDictionary<string, object?> dictionary) => dictionary switch
    {
        null => throw new ArgumentNullException(nameof(dictionary)),
        AnthropicMetadata metadata => metadata,
        IDictionary<string, object?> metadata => new AnthropicMetadata(metadata),
        _ => new AnthropicMetadata(dictionary.ToDictionary(pair => pair.Key, pair => pair.Value))
    };

    private void SetValueInDictionary(object? value, string propertyName)
        => this.Dictionary[propertyName] = value;

    private object? GetValueFromDictionary(string propertyName)
        => this.Dictionary.TryGetValue(propertyName, out var value) ? value : null;
}
