// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Pinecone;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// Represents a collection of vector store records in a Pinecone database, mapped to a dynamic <c>Dictionary&lt;string, object?&gt;</c>.
/// </summary>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public sealed class PineconeDynamicCollection : PineconeCollection<object, Dictionary<string, object?>>
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
{
    /// <summary>
    /// Initializes a new instance of the <see cref="PineconeDynamicCollection"/> class.
    /// </summary>
    /// <param name="pineconeClient">Pinecone client that can be used to manage the collections and vectors in a Pinecone store.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    public PineconeDynamicCollection(PineconeClient pineconeClient, string name, PineconeCollectionOptions options)
        : base(
            pineconeClient,
            name,
            static options => new PineconeModelBuilder()
                .BuildDynamic(
                    options.Definition ?? throw new ArgumentException("Definition is required for dynamic collections"),
                    options.EmbeddingGenerator),
            options)
    {
    }
}
