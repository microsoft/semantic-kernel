// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.MistralAI.Client;

internal readonly struct ContentChunkType : IEquatable<ContentChunkType>
{
    public static ContentChunkType Text { get; } = new("text");

    public static ContentChunkType ImageUrl { get; } = new("image_url");

    public static ContentChunkType DocumentUrl { get; } = new("document_url");

    public string Type { get; }

    /// <summary>
    /// Creates a new <see cref="ContentChunkType"/> instance with the provided type.
    /// </summary>
    /// <param name="type">The label to associate with this <see cref="ContentChunkType"/>.</param>
    [JsonConstructor]
    public ContentChunkType(string type)
    {
        Verify.NotNullOrWhiteSpace(type, nameof(type));
        this.Type = type!;
    }

    /// <summary>
    /// Returns a value indicating whether two <see cref="ContentChunkType"/> instances are equivalent, as determined by a
    /// case-insensitive comparison of their labels.
    /// </summary>
    /// <param name="left"> the first <see cref="ContentChunkType"/> instance to compare </param>
    /// <param name="right"> the second <see cref="ContentChunkType"/> instance to compare </param>
    /// <returns> true if left and right are both null or have equivalent labels; false otherwise </returns>
    public static bool operator ==(ContentChunkType left, ContentChunkType right)
        => left.Equals(right);

    /// <summary>
    /// Returns a value indicating whether two <see cref="ContentChunkType"/> instances are not equivalent, as determined by a
    /// case-insensitive comparison of their labels.
    /// </summary>
    /// <param name="left"> the first <see cref="ContentChunkType"/> instance to compare </param>
    /// <param name="right"> the second <see cref="ContentChunkType"/> instance to compare </param>
    /// <returns> false if left and right are both null or have equivalent labels; true otherwise </returns>
    public static bool operator !=(ContentChunkType left, ContentChunkType right)
        => !left.Equals(right);

    /// <inheritdoc/>
    public override bool Equals([NotNullWhen(true)] object? obj)
        => obj is ContentChunkType otherRole && this == otherRole;

    /// <inheritdoc/>
    public bool Equals(ContentChunkType other)
        => string.Equals(this.Type, other.Type, StringComparison.OrdinalIgnoreCase);

    /// <inheritdoc/>
    public override int GetHashCode()
        => StringComparer.OrdinalIgnoreCase.GetHashCode(this.Type);

    /// <inheritdoc/>
    public override string ToString() => this.Type;
}
