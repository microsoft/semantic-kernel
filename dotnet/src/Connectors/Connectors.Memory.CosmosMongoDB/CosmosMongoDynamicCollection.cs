﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.Connectors.MongoDB;
using MongoDB.Driver;

namespace Microsoft.SemanticKernel.Connectors.CosmosMongoDB;

/// <summary>
/// Represents a collection of vector store records in a Mongo database, mapped to a dynamic <c>Dictionary&lt;string, object?&gt;</c>.
/// </summary>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public sealed class CosmosMongoDynamicCollection : CosmosMongoCollection<object, Dictionary<string, object?>>
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
{
    /// <summary>
    /// Initializes a new instance of the <see cref="CosmosMongoDynamicCollection"/> class.
    /// </summary>
    /// <param name="mongoDatabase"><see cref="IMongoDatabase"/> that can be used to manage the collections in MongoDB.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    public CosmosMongoDynamicCollection(IMongoDatabase mongoDatabase, string name, CosmosMongoCollectionOptions options)
        : base(
            mongoDatabase,
            name,
            static options => new MongoModelBuilder()
                .BuildDynamic(
                    options.VectorStoreRecordDefinition ?? throw new ArgumentException("VectorStoreRecordDefinition is required for dynamic collections"),
                    options.EmbeddingGenerator),
            options)
    {
    }
}
