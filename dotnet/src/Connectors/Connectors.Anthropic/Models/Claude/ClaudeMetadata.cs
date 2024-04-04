// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;

namespace Microsoft.SemanticKernel.Connectors.Anthropic;

/// <summary>
/// Represents the metadata associated with a Claude response.
/// </summary>
public sealed class ClaudeMetadata : ReadOnlyDictionary<string, object?>
{
    internal ClaudeMetadata() : base(new Dictionary<string, object?>()) { }

    private ClaudeMetadata(IDictionary<string, object?> dictionary) : base(dictionary) { }

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
    public ClaudeFinishReason? FinishReason
    {
        get => (ClaudeFinishReason?)this.GetValueFromDictionary(nameof(this.FinishReason));
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
    public int InputTokenCount
    {
        get => (this.GetValueFromDictionary(nameof(this.InputTokenCount)) as int?) ?? 0;
        internal init => this.SetValueInDictionary(value, nameof(this.InputTokenCount));
    }

    /// <summary>
    /// The number of output tokens which were used.
    /// </summary>
    public int OutputTokenCount
    {
        get => (this.GetValueFromDictionary(nameof(this.OutputTokenCount)) as int?) ?? 0;
        internal init => this.SetValueInDictionary(value, nameof(this.OutputTokenCount));
    }

    /// <summary>
    /// Converts a dictionary to a <see cref="ClaudeMetadata"/> object.
    /// </summary>
    public static ClaudeMetadata FromDictionary(IReadOnlyDictionary<string, object?> dictionary) => dictionary switch
    {
        null => throw new ArgumentNullException(nameof(dictionary)),
        ClaudeMetadata metadata => metadata,
        IDictionary<string, object?> metadata => new ClaudeMetadata(metadata),
        _ => new ClaudeMetadata(dictionary.ToDictionary(pair => pair.Key, pair => pair.Value))
    };

    private void SetValueInDictionary(object? value, string propertyName)
        => this.Dictionary[propertyName] = value;

    private object? GetValueFromDictionary(string propertyName)
        => this.Dictionary.TryGetValue(propertyName, out var value) ? value : null;
}
