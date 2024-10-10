<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
﻿// Copyright (c) Microsoft. All rights reserved.
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> Stashed changes
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> Stashed changes
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> Stashed changes
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> Stashed changes
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> Stashed changes
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> origin/main
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> Stashed changes

using System;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.ChatCompletion;
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
>>>>>>> origin/main
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
using System.ComponentModel;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.AI.ChatCompletion;
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

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
    /// Gets the label associated with this <see cref="AuthorRole"/>.
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
>>>>>>> origin/main
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
    public static readonly AuthorRole System = new("system");
    /// <summary>
    /// The role that provides responses to system-instructed, user-prompted input.
    /// </summary>
    public static readonly AuthorRole Assistant = new("assistant");
    /// <summary>
    /// The role that provides input for chat completions.
    /// </summary>
    public static readonly AuthorRole User = new("user");

    /// <summary>
    /// Gets the label associated with this AuthorRole.
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    /// </summary>
    /// <remarks>
    /// The label is what will be serialized into the "role" message field of the Chat Message format.
    /// </remarks>
    public string Label { get; }

    /// <summary>
    /// Creates a new <see cref="AuthorRole"/> instance with the provided label.
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
    /// </summary>
    /// <param name="label">The label to associate with this <see cref="AuthorRole"/>.</param>
    [JsonConstructor]
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
    /// </summary>
    /// <param name="label">The label to associate with this <see cref="AuthorRole"/>.</param>
    [JsonConstructor]
    public AuthorRole(string label)
    {
        Verify.NotNullOrWhiteSpace(label, nameof(label));
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    /// Creates a new AuthorRole instance with the provided label.
    /// </summary>
    /// <param name="label"></param>
>>>>>>> origin/main
=======
=======
>>>>>>> Stashed changes
    /// Creates a new AuthorRole instance with the provided label.
    /// </summary>
    /// <param name="label"></param>
>>>>>>> origin/main
    public AuthorRole(string label)
    {
        Verify.NotNullOrWhiteSpace(label, nameof(label));
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        this.Label = label!;
    }

    /// <summary>
    /// Returns a value indicating whether two <see cref="AuthorRole"/> instances are equivalent, as determined by a
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
    /// case-insensitive comparison of their labels.
    /// </summary>
    /// <param name="left"> the first <see cref="AuthorRole"/> instance to compare </param>
    /// <param name="right"> the second <see cref="AuthorRole"/> instance to compare </param>
    /// <returns> true if left and right are both null or have equivalent labels; false otherwise </returns>
    public static bool operator ==(AuthorRole left, AuthorRole right)
        => left.Equals(right);

    /// <summary>
    /// Returns a value indicating whether two <see cref="AuthorRole"/> instances are not equivalent, as determined by a
    /// case-insensitive comparison of their labels.
    /// </summary>
    /// <param name="left"> the first <see cref="AuthorRole"/> instance to compare </param>
    /// <param name="right"> the second <see cref="AuthorRole"/> instance to compare </param>
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
    /// Returns a value indicating whether two AuthorRole instances are equivalent, as determined by a
>>>>>>> origin/main
    /// case-insensitive comparison of their labels.
    /// </summary>
    /// <param name="left"> the first <see cref="AuthorRole"/> instance to compare </param>
    /// <param name="right"> the second <see cref="AuthorRole"/> instance to compare </param>
    /// <returns> true if left and right are both null or have equivalent labels; false otherwise </returns>
    public static bool operator ==(AuthorRole left, AuthorRole right)
<<<<<<< main
        => left.Equals(right);
=======
    {
        if (Object.ReferenceEquals(left, right))
        {
            return true;
        }

        if (Object.ReferenceEquals(left, null) || Object.ReferenceEquals(right, null))
        {
            return false;
        }

        return left.Equals(right);
    }
>>>>>>> origin/main

    /// <summary>
    /// Returns a value indicating whether two <see cref="AuthorRole"/> instances are not equivalent, as determined by a
    /// case-insensitive comparison of their labels.
    /// </summary>
    /// <param name="left"> the first <see cref="AuthorRole"/> instance to compare </param>
    /// <param name="right"> the second <see cref="AuthorRole"/> instance to compare </param>
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    /// <returns> false if left and right are both null or have equivalent labels; true otherwise </returns>
    public static bool operator !=(AuthorRole left, AuthorRole right)
        => !(left == right);

    /// <inheritdoc/>
    public override bool Equals([NotNullWhen(true)] object? obj)
        => obj is AuthorRole otherRole && this == otherRole;

    /// <inheritdoc/>
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
    public bool Equals(AuthorRole other)
        => string.Equals(this.Label, other.Label, StringComparison.OrdinalIgnoreCase);

    /// <inheritdoc/>
    public override int GetHashCode()
        => StringComparer.OrdinalIgnoreCase.GetHashCode(this.Label);
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
    [EditorBrowsable(EditorBrowsableState.Never)]
    public override bool Equals(object obj)
        => obj is AuthorRole otherRole && this == otherRole;

    /// <inheritdoc/>
    [EditorBrowsable(EditorBrowsableState.Never)]
    public override int GetHashCode()
        => this.Label.GetHashCode();

    /// <inheritdoc/>
>>>>>>> origin/main
    public bool Equals(AuthorRole other)
        => !Object.ReferenceEquals(other, null)
            && string.Equals(this.Label, other.Label, StringComparison.OrdinalIgnoreCase);
<<<<<<< Updated upstream
<<<<<<< head
=======
>>>>>>> Stashed changes

    /// <inheritdoc/>
    public override int GetHashCode()
        => StringComparer.OrdinalIgnoreCase.GetHashCode(this.Label);
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes

    /// <inheritdoc/>
    public override string ToString() => this.Label;
}
