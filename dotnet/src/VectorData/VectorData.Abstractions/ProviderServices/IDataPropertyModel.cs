// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.Extensions.VectorData.ProviderServices;

/// <summary>
/// Represents a read-only view of a data property on a vector store record.
/// This is an internal support type meant for use by connectors only and not by applications.
/// </summary>
[Experimental("MEVD9001")]
public interface IDataPropertyModel : IPropertyModel
{
    /// <summary>
    /// Gets a value indicating whether this data property is indexed.
    /// </summary>
    bool IsIndexed { get; }

    /// <summary>
    /// Gets a value indicating whether this data property is indexed for full-text search.
    /// </summary>
    bool IsFullTextIndexed { get; }
}
