// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// Represents the context for an operation selection predicate.
/// </summary>
public readonly struct OperationSelectionPredicateContext : IEquatable<OperationSelectionPredicateContext>
{
    /// <summary>
    /// Initializes a new instance of the <see cref="OperationSelectionPredicateContext"/> struct.
    /// </summary>
    /// <param name="Id">The identifier for the operation.</param>
    /// <param name="Path">The path of the operation.</param>
    /// <param name="Method">The HTTP method (GET, POST, etc.) of the operation.</param>
    /// <param name="Description">The description of the operation.</param>
    internal OperationSelectionPredicateContext(string? Id, string Path, string Method, string? Description)
    {
        this.Id = Id;
        this.Path = Path;
        this.Method = Method;
        this.Description = Description;
    }

    /// <summary>
    /// The identifier for the operation.
    /// </summary>
    public string? Id { get; }

    /// <summary>
    /// The path of the operation.
    /// </summary>
    public string Path { get; }

    /// <summary>
    /// The HTTP method (GET, POST, etc.) of the operation.
    /// </summary>
    public string Method { get; }

    /// <summary>
    /// The description of the operation.
    /// </summary>
    public string? Description { get; }

    /// <inheritdoc />
    public override bool Equals(object? obj)
    {
        return obj is OperationSelectionPredicateContext other && this.Equals(other);
    }

    /// <inheritdoc />
    public override int GetHashCode()
    {
        // Using a tuple to create a hash code based on the properties  
        return HashCode.Combine(this.Id, this.Path, this.Method, this.Description);
    }

    /// <inheritdoc />
    public static bool operator ==(OperationSelectionPredicateContext left, OperationSelectionPredicateContext right)
    {
        return left.Equals(right);
    }

    /// <inheritdoc />
    public static bool operator !=(OperationSelectionPredicateContext left, OperationSelectionPredicateContext right)
    {
        return !(left == right);
    }

    /// <inheritdoc />
    public bool Equals(OperationSelectionPredicateContext other)
    {
        return this.Id == other.Id &&
               this.Path == other.Path &&
               this.Method == other.Method &&
               this.Description == other.Description;
    }
}
