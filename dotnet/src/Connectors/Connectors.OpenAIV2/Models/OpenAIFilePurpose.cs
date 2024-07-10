// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Defines the purpose associated with the uploaded file:
/// https://platform.openai.com/docs/api-reference/files/object#files/object-purpose
/// </summary>
[Experimental("SKEXP0010")]
[Obsolete("Use OpenAI SDK or AzureOpenAI SDK clients for file operations. This class is deprecated and will be removed in a future version.")]
[ExcludeFromCodeCoverage]
public readonly struct OpenAIFilePurpose : IEquatable<OpenAIFilePurpose>
{
    /// <summary>
    /// File to be used by assistants as input.
    /// </summary>
    public static OpenAIFilePurpose Assistants { get; } = new("assistants");

    /// <summary>
    /// File produced as assistants output.
    /// </summary>
    public static OpenAIFilePurpose AssistantsOutput { get; } = new("assistants_output");

    /// <summary>
    /// Files uploaded as a batch of API requests
    /// </summary>
    public static OpenAIFilePurpose Batch { get; } = new("batch");

    /// <summary>
    /// File produced as result of a file included as a batch request.
    /// </summary>
    public static OpenAIFilePurpose BatchOutput { get; } = new("batch_output");

    /// <summary>
    /// File to be used as input to fine-tune a model.
    /// </summary>
    public static OpenAIFilePurpose FineTune { get; } = new("fine-tune");

    /// <summary>
    /// File produced as result of fine-tuning a model.
    /// </summary>
    public static OpenAIFilePurpose FineTuneResults { get; } = new("fine-tune-results");

    /// <summary>
    /// File to be used for Assistants image file inputs.
    /// </summary>
    public static OpenAIFilePurpose Vision { get; } = new("vision");

    /// <summary>
    /// Gets the label associated with this <see cref="OpenAIFilePurpose"/>.
    /// </summary>
    public string Label { get; }

    /// <summary>
    /// Creates a new <see cref="OpenAIFilePurpose"/> instance with the provided label.
    /// </summary>
    /// <param name="label">The label to associate with this <see cref="OpenAIFilePurpose"/>.</param>
    public OpenAIFilePurpose(string label)
    {
        Verify.NotNullOrWhiteSpace(label, nameof(label));
        this.Label = label!;
    }

    /// <summary>
    /// Returns a value indicating whether two <see cref="OpenAIFilePurpose"/> instances are equivalent, as determined by a
    /// case-insensitive comparison of their labels.
    /// </summary>
    /// <param name="left"> the first <see cref="OpenAIFilePurpose"/> instance to compare </param>
    /// <param name="right"> the second <see cref="OpenAIFilePurpose"/> instance to compare </param>
    /// <returns> true if left and right are both null or have equivalent labels; false otherwise </returns>
    public static bool operator ==(OpenAIFilePurpose left, OpenAIFilePurpose right)
        => left.Equals(right);

    /// <summary>
    /// Returns a value indicating whether two <see cref="OpenAIFilePurpose"/> instances are not equivalent, as determined by a
    /// case-insensitive comparison of their labels.
    /// </summary>
    /// <param name="left"> the first <see cref="OpenAIFilePurpose"/> instance to compare </param>
    /// <param name="right"> the second <see cref="OpenAIFilePurpose"/> instance to compare </param>
    /// <returns> false if left and right are both null or have equivalent labels; true otherwise </returns>
    public static bool operator !=(OpenAIFilePurpose left, OpenAIFilePurpose right)
        => !(left == right);

    /// <inheritdoc/>
    public override bool Equals([NotNullWhen(true)] object? obj)
        => obj is OpenAIFilePurpose otherPurpose && this == otherPurpose;

    /// <inheritdoc/>
    public bool Equals(OpenAIFilePurpose other)
        => string.Equals(this.Label, other.Label, StringComparison.OrdinalIgnoreCase);

    /// <inheritdoc/>
    public override int GetHashCode()
        => StringComparer.OrdinalIgnoreCase.GetHashCode(this.Label);

    /// <inheritdoc/>
    public override string ToString() => this.Label;
}
