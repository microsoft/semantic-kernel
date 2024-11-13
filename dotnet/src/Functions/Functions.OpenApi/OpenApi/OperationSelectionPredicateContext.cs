// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// Represents the context for an operation selection predicate.
/// </summary>
public readonly record struct OperationSelectionPredicateContext
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
}
