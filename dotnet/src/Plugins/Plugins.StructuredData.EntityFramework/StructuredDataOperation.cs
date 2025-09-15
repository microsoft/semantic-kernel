// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A description of the supported database operations within a structured data service.
/// </summary>
public readonly struct StructuredDataOperation : IEquatable<StructuredDataOperation>
{
    /// <summary>
    /// The operation for selecting/querying data from the database.
    /// </summary>
    public static StructuredDataOperation Select { get; } = new("Select");

    /// <summary>
    /// The operation for inserting data into the database.
    /// </summary>
    public static StructuredDataOperation Insert { get; } = new("Insert");

    /// <summary>
    /// The operation for updating data in the database.
    /// </summary>
    public static StructuredDataOperation Update { get; } = new("Update");

    /// <summary>
    /// The operation for deleting data from the database.
    /// </summary>
    public static StructuredDataOperation Delete { get; } = new("Delete");

    /// <summary>
    /// The default set of supported operations.
    /// </summary>
    public static readonly HashSet<StructuredDataOperation> Default = new()
    {
        Select,
        Insert,
        Update,
        Delete
    };

    /// <summary>
    /// Gets the label associated with this <see cref="StructuredDataOperation"/>.
    /// </summary>
    public string Label { get; }

    /// <summary>
    /// Creates a new <see cref="StructuredDataOperation"/> instance with the provided label.
    /// </summary>
    /// <param name="label">The label to associate with this operation.</param>
    public StructuredDataOperation(string label)
    {
        Verify.NotNullOrWhiteSpace(label);
        this.Label = label;
    }

    /// <summary>
    /// Compares two <see cref="StructuredDataOperation"/> instances for equality.
    /// </summary>
    public static bool operator ==(StructuredDataOperation left, StructuredDataOperation right)
        => left.Equals(right);

    /// <summary>
    /// Compares two <see cref="StructuredDataOperation"/> instances for inequality.
    /// </summary>
    public static bool operator !=(StructuredDataOperation left, StructuredDataOperation right)
        => !(left == right);

    /// <inheritdoc/>
    public override bool Equals(object? obj)
        => obj is StructuredDataOperation other && this == other;

    /// <inheritdoc/>
    public bool Equals(StructuredDataOperation other)
        => string.Equals(this.Label, other.Label, StringComparison.OrdinalIgnoreCase);

    /// <inheritdoc/>
    public override int GetHashCode()
        => StringComparer.OrdinalIgnoreCase.GetHashCode(this.Label);

    /// <inheritdoc/>
    public override string ToString() => this.Label;
}
