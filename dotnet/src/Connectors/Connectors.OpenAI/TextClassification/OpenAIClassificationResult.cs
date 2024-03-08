// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Runtime.CompilerServices;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Represents the result of an OpenAI text classification.
/// </summary>
public sealed class OpenAIClassificationResult : ReadOnlyDictionary<string, object?>
{
    internal OpenAIClassificationResult(
        bool flagged,
        IReadOnlyList<OpenAIClassificationEntry> entries)
        : base(new Dictionary<string, object?>())
    {
        this.Flagged = flagged;
        this.Entries = entries;
    }

    /// <summary>
    /// Whether the content violates OpenAI's usage policies.
    /// </summary>
    public bool Flagged
    {
        get => this.GetValueFromDictionary() as bool? ?? false;
        private init => this.SetValueInDictionary(value);
    }

    /// <summary>
    /// A list of entries with category, their scores, and whether they are flagged or not.
    /// </summary>
    public IReadOnlyList<OpenAIClassificationEntry> Entries
    {
        get => (this.GetValueFromDictionary() as IReadOnlyList<OpenAIClassificationEntry>)!;
        private init => this.SetValueInDictionary(value);
    }

    private void SetValueInDictionary(object? value, [CallerMemberName] string propertyName = "")
        => this.Dictionary[propertyName] = value;

    private object? GetValueFromDictionary([CallerMemberName] string propertyName = "")
        => this.Dictionary.TryGetValue(propertyName, out var value) ? value : null;
}
