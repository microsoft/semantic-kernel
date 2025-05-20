// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Pinecone;
using Pinecone;
using Xunit;

namespace SemanticKernel.Connectors.Pinecone.UnitTests;

/// <summary>
/// Contains tests for the <see cref="PineconeCollection{TKey, TRecord}"/> class.
/// </summary>
public class PineconeCollectionTests
{
    private const string TestCollectionName = "testcollection";

    /// <summary>
    /// Tests that the collection can be created even if the definition and the type do not match.
    /// In this case, the expectation is that a custom mapper will be provided to map between the
    /// schema as defined by the definition and the different data model.
    /// </summary>
    [Fact]
    public void CanCreateCollectionWithMismatchedDefinitionAndType()
    {
        // Arrange.
        var definition = new VectorStoreCollectionDefinition()
        {
            Properties = new List<VectorStoreProperty>
            {
                new VectorStoreKeyProperty("Key", typeof(string)),
                new VectorStoreDataProperty("OriginalNameData", typeof(string)),
                new VectorStoreVectorProperty("Vector", typeof(ReadOnlyMemory<float>?), 4),
            }
        };
        var pineconeClient = new PineconeClient("fake api key");

        // Act.
        using var sut = new PineconeCollection<string, SinglePropsModel>(
            pineconeClient,
            TestCollectionName,
            new() { Definition = definition });
    }

    public sealed class SinglePropsModel
    {
        public string Key { get; set; } = string.Empty;

        public string OriginalNameData { get; set; } = string.Empty;

        public string Data { get; set; } = string.Empty;

        public ReadOnlyMemory<float>? Vector { get; set; }
    }
}
