// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Pinecone;
using Moq;
using Xunit;
using Sdk = Pinecone;

namespace SemanticKernel.Connectors.Pinecone.UnitTests;

/// <summary>
/// Contains tests for the <see cref="PineconeVectorStoreRecordCollection{TRecord}"/> class.
/// </summary>
public class PineconeVectorStoreRecordCollectionTests
{
    private const string TestCollectionName = "testcollection";

#pragma warning disable CS0618 // IVectorStoreRecordMapper is obsolete
    /// <summary>
    /// Tests that the collection can be created even if the definition and the type do not match.
    /// In this case, the expectation is that a custom mapper will be provided to map between the
    /// schema as defined by the definition and the different data model.
    /// </summary>
    [Fact]
    public void CanCreateCollectionWithMismatchedDefinitionAndType()
    {
        // Arrange.
        var definition = new VectorStoreRecordDefinition()
        {
            Properties = new List<VectorStoreRecordProperty>
            {
                new VectorStoreRecordKeyProperty("Key", typeof(string)),
                new VectorStoreRecordDataProperty("OriginalNameData", typeof(string)),
                new VectorStoreRecordVectorProperty("Vector", typeof(ReadOnlyMemory<float>?), 4),
            }
        };
        var pineconeClient = new Sdk.PineconeClient("fake api key");

        // Act.
        var sut = new PineconeVectorStoreRecordCollection<SinglePropsModel>(
            pineconeClient,
            TestCollectionName,
            new() { VectorStoreRecordDefinition = definition, VectorCustomMapper = Mock.Of<IVectorStoreRecordMapper<SinglePropsModel, Sdk.Vector>>() });
    }
#pragma warning restore CS0618

    public sealed class SinglePropsModel
    {
        public string Key { get; set; } = string.Empty;

        public string OriginalNameData { get; set; } = string.Empty;

        public string Data { get; set; } = string.Empty;

        public ReadOnlyMemory<float>? Vector { get; set; }
    }
}
