// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Represents the kind of annotation that can be associated with a message.
/// </summary>
public readonly struct AnnotationKind : IEquatable<AnnotationKind>
{
    /// <summary>
    /// Annotation kind representing a citation to a file.
    /// </summary>
    public static AnnotationKind FileCitation { get; } = new("filecitation");

    /// <summary>
    /// Annotation kind representing a citation to a text segment.
    /// </summary>
    public static AnnotationKind TextCitation { get; } = new("textcitation");

    /// <summary>
    /// Annotation kind representing a citation to a URL.
    /// </summary>
    public static AnnotationKind UrlCitation { get; } = new("urlcitation");

    /// <summary>
    /// Gets the label associated with this <see cref="AnnotationKind"/>.
    /// </summary>
    /// <remarks>
    /// The label is what will be serialized into the "kind" field of the annotation content item.
    /// </remarks>
    public string Label { get; }

    /// <summary>
    /// Creates a new <see cref="AnnotationKind"/> instance with the provided label.
    /// </summary>
    /// <param name="label">The label to associate with this <see cref="AnnotationKind"/>.</param>
    [JsonConstructor]
    public AnnotationKind(string label)
    {
        Verify.NotNullOrWhiteSpace(label, nameof(label));
        this.Label = label!;
    }

    /// <summary>
    /// Returns a value indicating whether two <see cref="AnnotationKind"/> instances are equivalent, as determined by a
    /// case-insensitive comparison of their labels.
    /// </summary>
    /// <param name="left"> the first <see cref="AnnotationKind"/> instance to compare </param>
    /// <param name="right"> the second <see cref="AnnotationKind"/> instance to compare </param>
    /// <returns> true if left and right are both null or have equivalent labels; false otherwise </returns>
    public static bool operator ==(AnnotationKind left, AnnotationKind right)
        => left.Equals(right);

    /// <summary>
    /// Returns a value indicating whether two <see cref="AnnotationKind"/> instances are not equivalent, as determined by a
    /// case-insensitive comparison of their labels.
    /// </summary>
    /// <param name="left"> the first <see cref="AnnotationKind"/> instance to compare </param>
    /// <param name="right"> the second <see cref="AnnotationKind"/> instance to compare </param>
    /// <returns> false if left and right are both null or have equivalent labels; true otherwise </returns>
    public static bool operator !=(AnnotationKind left, AnnotationKind right)
        => !(left == right);

    /// <inheritdoc/>
    public override bool Equals([NotNullWhen(true)] object? obj)
        => obj is AnnotationKind otherRole && this == otherRole;

    /// <inheritdoc/>
    public bool Equals(AnnotationKind other)
        => string.Equals(this.Label, other.Label, StringComparison.OrdinalIgnoreCase);

    /// <inheritdoc/>
    public override int GetHashCode()
        => StringComparer.OrdinalIgnoreCase.GetHashCode(this.Label);

    /// <inheritdoc/>
    public override string ToString() => this.Label;
}
