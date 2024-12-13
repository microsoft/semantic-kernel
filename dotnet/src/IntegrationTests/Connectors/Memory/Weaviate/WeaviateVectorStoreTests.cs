// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Connectors.Weaviate;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Weaviate;

[Collection("WeaviateVectorStoreCollection")]
public sealed class WeaviateVectorStoreTests(WeaviateVectorStoreFixture fixture)
    : BaseVectorStoreTests<Guid, WeaviateHotel>(new WeaviateVectorStore(fixture.HttpClient!))
{ }
