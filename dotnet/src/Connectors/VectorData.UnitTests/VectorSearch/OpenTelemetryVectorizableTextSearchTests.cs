// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Moq;
using OpenTelemetry.Trace;
using Xunit;

namespace VectorData.UnitTests.VectorSearch;

public class OpenTelemetryVectorizableTextSearchTests
{
    [Fact]
    public async Task VectorizableTextSearchWorksWithActivityAsync()
    {
        // Arrange
        var sourceName = Guid.NewGuid().ToString();
        var expectedResults = new VectorSearchResults<string>(new List<VectorSearchResult<string>> { new("record1", 0.90f) }.ToAsyncEnumerable());

        var mockInnerSearch = new Mock<IVectorizableTextSearch<string>>();

        mockInnerSearch
            .Setup(s => s.VectorizableTextSearchAsync("test query", null, default))
            .ReturnsAsync(expectedResults);

        mockInnerSearch
            .Setup(s => s.GetService(typeof(VectorStoreRecordCollectionMetadata), It.IsAny<object?>()))
            .Returns(new VectorStoreRecordCollectionMetadata
            {
                VectorStoreSystemName = "testvectorstore",
                DatabaseName = "testdb",
                CollectionName = "testcollection"
            });

        var innerSearch = mockInnerSearch.Object;
        var vectorizableTextSearch = innerSearch
            .AsBuilder()
            .UseOpenTelemetry(sourceName)
            .Build();

        var activities = new List<Activity>();
        using var tracerProvider = OpenTelemetry.Sdk.CreateTracerProviderBuilder()
            .AddSource(sourceName)
            .AddInMemoryExporter(activities)
            .Build();

        // Act
        var result = await vectorizableTextSearch.VectorizableTextSearchAsync("test query");

        // Assert
        Assert.Equal(expectedResults, result);

        var activity = Assert.Single(activities);

        Assert.Equal("vectorizable_text_search testcollection", activity.DisplayName);
        Assert.Equal("vectorizable_text_search", activity.GetTagItem("db.operation.name"));
        Assert.Equal("testdb", activity.GetTagItem("db.namespace"));
        Assert.Equal("testcollection", activity.GetTagItem("db.collection.name"));
        Assert.Equal("testvectorstore", activity.GetTagItem("db.system.name"));
    }
}
