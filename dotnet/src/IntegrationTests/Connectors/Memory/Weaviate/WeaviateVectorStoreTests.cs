// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.Connectors.Weaviate;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Weaviate;

[Collection("WeaviateVectorStoreCollection")]
public sealed class WeaviateVectorStoreTests(WeaviateVectorStoreFixture fixture)
    : BaseVectorStoreTests<Guid, WeaviateHotel>(new WeaviateVectorStore(fixture.HttpClient!))
{
    // Weaviate requires each collection name to start with uppercase ASCII letter.
    protected override IEnumerable<string> CollectionNames => ["Listcollectionnames1", "Listcollectionnames2", "Listcollectionnames3"];
}
