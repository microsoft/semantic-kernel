// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Postgres;
using Npgsql;
using Xunit;

namespace SemanticKernel.Connectors.Postgres.UnitTests;

public class PostgresCollectionTests
{
    private const string TestCollectionName = "testcollection";

    [Fact]
    public void ThrowsForUnsupportedType()
    {
        // Arrange
        var recordDefinition = new VectorStoreRecordDefinition
        {
            Properties = [
                new VectorStoreKeyProperty("HotelId", typeof(ulong)),
                new VectorStoreDataProperty("HotelName", typeof(string)) { IsIndexed = true, IsFullTextIndexed = true },
            ]
        };
        var options = new PostgresCollectionOptions<Dictionary<string, object?>>()
        {
            VectorStoreRecordDefinition = recordDefinition
        };
        NpgsqlDataSourceBuilder dataSourceBuilder = new("Host=localhost;Database=test;");
        dataSourceBuilder.UseVector();
        using var source = dataSourceBuilder.Build();

        // Act & Assert
        Assert.Throws<NotSupportedException>(() => new PostgresCollection<object, Dictionary<string, object?>>(source, TestCollectionName, options));
    }
}
