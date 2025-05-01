// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;

namespace GettingStartedWithVectorStores;

/// <summary>
/// Sample model class that represents a glossary entry.
/// </summary>
/// <remarks>
/// Note that each property is decorated with an attribute that specifies how the property should be treated by the vector store.
/// This allows us to create a collection in the vector store and upsert and retrieve instances of this class without any further configuration.
/// </remarks>
internal sealed class Glossary
{
    [VectorStoreKeyProperty]
    public string Key { get; set; }

    [VectorStoreDataProperty(IsIndexed = true)]
    public string Category { get; set; }

    [VectorStoreDataProperty]
    public string Term { get; set; }

    [VectorStoreDataProperty]
    public string Definition { get; set; }

    [VectorStoreVectorProperty(Dimensions: 1536)]
    public ReadOnlyMemory<float> DefinitionEmbedding { get; set; }
}
