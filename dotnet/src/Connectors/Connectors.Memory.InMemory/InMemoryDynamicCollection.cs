// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Connectors.InMemory;

/// <summary>
/// Represents a collection of vector store records in a InMemory database, mapped to a dynamic <c>Dictionary&lt;string, object?&gt;</c>.
/// </summary>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public sealed class InMemoryDynamicCollection : InMemoryCollection<object, Dictionary<string, object?>>
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
{
    /// <summary>
    /// Initializes a new instance of the <see cref="InMemoryDynamicCollection"/> class.
    /// </summary>
    /// <param name="name">The name of the collection.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    [RequiresUnreferencedCode("The InMemory provider is incompatible with trimming.")]
    [RequiresDynamicCode("The InMemory provider is incompatible with NativeAOT.")]
    public InMemoryDynamicCollection(string name, InMemoryCollectionOptions options)
        : base(
            internalCollection: null,
            internalCollectionTypes: null,
            name,
            static options => new InMemoryModelBuilder().BuildDynamic(
                options.Definition ?? throw new ArgumentException("Definition is required for dynamic collections"),
                options.EmbeddingGenerator),
            options)
    {
    }

    internal InMemoryDynamicCollection(
        ConcurrentDictionary<string, ConcurrentDictionary<object, object>> internalCollection,
        ConcurrentDictionary<string, Type> internalCollectionTypes,
        string name,
        InMemoryCollectionOptions options)
        : base(
            internalCollection,
            internalCollectionTypes,
            name,
            static options => new InMemoryModelBuilder().BuildDynamic(
                options.Definition ?? throw new ArgumentException("Definition is required for dynamic collections"),
                options.EmbeddingGenerator),
            options)
    {
    }
}
