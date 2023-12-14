// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.ChatCompletion;

/// <summary>
/// A description of the intended purpose of a message within a chat completions interaction.
/// </summary>
public readonly struct AuthorRole : IEquatable<AuthorRole>
{
    /// <summary>
    /// The role that instructs or sets the behavior of the assistant.
    /// </summary>
    public static AuthorRole System { get; } = new("system");

    /// <summary>
    /// The role that provides responses to system-instructed, user-prompted input.
    /// </summary>
    public static AuthorRole Assistant { get; } = new("assistant");

    /// <summary>
    /// The role that provides input for chat completions.
    /// </summary>
    public static AuthorRole User { get; } = new("user");

    /// <summary>
    /// The role that provides additional information and references for chat completions.
    /// </summary>
    public static AuthorRole Tool { get; } = new("tool");

    /// <summary>
    /// Gets the label associated with this AuthorRole.
    /// </summary>
    /// <remarks>
    /// The label is what will be serialized into the "role" message field of the Chat Message format.
    /// </remarks>
    public string Label { get; }

    /// <summary>
    /// Creates a new AuthorRole instance with the provided label.
    /// </summary>
    /// <param name="label">The label to associate with this AuthorRole.</param>
    [JsonConstructor]
    public AuthorRole(string label)
    {
        Verify.NotNullOrWhiteSpace(label, nameof(label));
        this.Label = label!;
    }

    /// <summary>
    /// Returns a value indicating whether two AuthorRole instances are equivalent, as determined by a
    /// case-insensitive comparison of their labels.
    /// </summary>
    /// <param name="left"> the first AuthorRole instance to compare </param>
    /// <param name="right"> the second AuthorRole instance to compare </param>
    /// <returns> true if left and right are both null or have equivalent labels; false otherwise </returns>
    public static bool operator ==(AuthorRole left, AuthorRole right)
        => left.Equals(right);

    /// <summary>
    /// Returns a value indicating whether two AuthorRole instances are not equivalent, as determined by a
    /// case-insensitive comparison of their labels.
    /// </summary>
    /// <param name="left"> the first AuthorRole instance to compare </param>
    /// <param name="right"> the second AuthorRole instance to compare </param>
    /// <returns> false if left and right are both null or have equivalent labels; true otherwise </returns>
    public static bool operator !=(AuthorRole left, AuthorRole right)
        => !(left == right);

    /// <inheritdoc/>
    public override bool Equals([NotNullWhen(true)] object? obj)
        => obj is AuthorRole otherRole && this == otherRole;

    /// <inheritdoc/>
    public bool Equals(AuthorRole other)
        => string.Equals(this.Label, other.Label, StringComparison.OrdinalIgnoreCase);

    /// <inheritdoc/>
    public override int GetHashCode()
        => StringComparer.OrdinalIgnoreCase.GetHashCode(this.Label ?? string.Empty);

    /// <inheritdoc/>
    public override string ToString() => this.Label ?? string.Empty;
}
