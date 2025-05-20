// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.PgVector;
using Xunit;

namespace SemanticKernel.Connectors.PgVector.UnitTests;

public class PostgresCollectionTests
{
    private const string TestCollectionName = "testcollection";

    [Fact]
    public void ThrowsForUnsupportedType()
    {
        // Arrange
        var recordDefinition = new VectorStoreCollectionDefinition
        {
            Properties = [
                new VectorStoreKeyProperty("HotelId", typeof(ulong)),
                new VectorStoreDataProperty("HotelName", typeof(string)) { IsIndexed = true, IsFullTextIndexed = true },
            ]
        };
        var options = new PostgresCollectionOptions()
        {
            Definition = recordDefinition
        };

        // Act & Assert
        Assert.Throws<NotSupportedException>(() => new PostgresDynamicCollection("Host=localhost;Database=test;", TestCollectionName, options));
    }
}
