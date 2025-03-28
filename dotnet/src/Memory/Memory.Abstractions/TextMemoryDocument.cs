// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// Represents a storage record for a single text based memory.
/// </summary>
public sealed class TextMemoryDocument
{
    /// <summary>
    /// Gets or sets a unique identifier for the memory document.
    /// </summary>
    public Guid Key { get; set; }

    /// <summary>
    /// Gets or sets the namespace for the memory document.
    /// </summary>
    /// <remarks>
    /// A namespace is a logical grouping of memory documents, e.g. may include a user id to scope the memory to a specific user.
    /// </remarks>
    public string Namespace { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets an optional name for the memory document.
    /// </summary>
    public string Name { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets an optional category for the memory document.
    /// </summary>
    public string Category { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the actual memory content as text.
    /// </summary>
    public string MemoryText { get; set; } = string.Empty;
}
