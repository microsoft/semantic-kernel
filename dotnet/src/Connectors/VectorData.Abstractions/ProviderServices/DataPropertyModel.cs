// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.Extensions.VectorData.ProviderServices;

/// <summary>
/// Represents a data property on a vector store record.
/// This is an internal support type meant for use by connectors only and not by applications.
/// </summary>
[Experimental("MEVD9001")]
public class DataPropertyModel(string modelName, Type type) : PropertyModel(modelName, type)
{
    /// <summary>
    /// Gets or sets a value indicating whether this data property is indexed.
    /// </summary>
    /// <value>
    /// The default is <see langword="false" />.
    /// </value>
    public bool IsIndexed { get; set; }

    /// <summary>
    /// Gets or sets a value indicating whether this data property is indexed for full-text search.
    /// </summary>
    /// <value>
    /// The default is <see langword="false" />.
    /// </value>
    public bool IsFullTextIndexed { get; set; }

    /// <inheritdoc/>
    public override string ToString()
        => $"{this.ModelName} (Data, {this.Type.Name})";
}
