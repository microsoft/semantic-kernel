// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Qdrant.Client;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

/// <summary>
/// Represents a collection of vector store records in a Qdrant database, mapped to a dynamic <c>Dictionary&lt;string, object?&gt;</c>.
/// </summary>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public sealed class QdrantDynamicCollection : QdrantCollection<object, Dictionary<string, object?>>
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
{
    /// <summary>
    /// Initializes a new instance of the <see cref="QdrantDynamicCollection"/> class.
    /// </summary>
    /// <param name="qdrantClient">Qdrant client that can be used to manage the collections and points in a Qdrant store.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="ownsClient">A value indicating whether <paramref name="qdrantClient"/> is disposed when the collection is disposed.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    public QdrantDynamicCollection(QdrantClient qdrantClient, string name, bool ownsClient, QdrantCollectionOptions options)
        : this(() => new MockableQdrantClient(qdrantClient, ownsClient), name, options)
    {
    }

    internal QdrantDynamicCollection(Func<MockableQdrantClient> clientFactory, string name, QdrantCollectionOptions options)
        : base(
            clientFactory,
            name,
            static options => new QdrantModelBuilder(options.HasNamedVectors)
                .BuildDynamic(
                    options.Definition ?? throw new ArgumentException("Definition is required for dynamic collections"),
                    options.EmbeddingGenerator),
            options)
    {
    }
}
