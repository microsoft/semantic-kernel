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

public class OpenTelemetryKeywordHybridSearchTests
{
    [Fact]
    public async Task HybridSearchWorksWithActivityAsync()
    {
        // Arrange
        var sourceName = Guid.NewGuid().ToString();
        var expectedResults = new VectorSearchResults<string>(new List<VectorSearchResult<string>> { new("record1", 0.95f) }.ToAsyncEnumerable());

        var mockInnerSearch = new Mock<IKeywordHybridSearch<string>>();

        mockInnerSearch
            .Setup(s => s.HybridSearchAsync(It.IsAny<float[]>(), It.IsAny<ICollection<string>>(), null, default))
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
        var keywordHybridSearch = innerSearch
            .AsBuilder()
            .UseOpenTelemetry(sourceName)
            .Build();

        var activities = new List<Activity>();
        using var tracerProvider = OpenTelemetry.Sdk.CreateTracerProviderBuilder()
            .AddSource(sourceName)
            .AddInMemoryExporter(activities)
            .Build();

        var vector = new float[] { 1.0f };

        // Act
        var result = await keywordHybridSearch.HybridSearchAsync(vector, ["keyword1"]);

        // Assert
        Assert.Equal(expectedResults, result);

        var activity = Assert.Single(activities);

        Assert.Equal("hybrid_search testcollection", activity.DisplayName);
        Assert.Equal("hybrid_search", activity.GetTagItem("db.operation.name"));
        Assert.Equal("testdb", activity.GetTagItem("db.namespace"));
        Assert.Equal("testcollection", activity.GetTagItem("db.collection.name"));
        Assert.Equal("testvectorstore", activity.GetTagItem("db.system.name"));
    }
}
