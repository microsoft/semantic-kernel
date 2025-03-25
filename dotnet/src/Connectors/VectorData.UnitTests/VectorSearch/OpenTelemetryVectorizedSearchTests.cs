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

public class OpenTelemetryVectorizedSearchTests
{
    [Fact]
    public async Task VectorizedSearchWorksWithActivityAsync()
    {
        // Arrange
        var sourceName = Guid.NewGuid().ToString();
        var expectedResults = new VectorSearchResults<string>(new List<VectorSearchResult<string>> { new("record1", 0.95f) }.ToAsyncEnumerable());

        var mockInnerSearch = new Mock<IVectorizedSearch<string>>();

        mockInnerSearch
            .Setup(s => s.VectorizedSearchAsync(It.IsAny<float[]>(), null, default))
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
        var vectorizedSearch = innerSearch
            .AsBuilder()
            .UseOpenTelemetry(sourceName)
            .Build();

        var activities = new List<Activity>();
        using var tracerProvider = OpenTelemetry.Sdk.CreateTracerProviderBuilder()
            .AddSource(sourceName)
            .AddInMemoryExporter(activities)
            .Build();

        var vector = new float[] { 1.0f, 2.0f };

        // Act
        var result = await vectorizedSearch.VectorizedSearchAsync(vector);

        // Assert
        Assert.Equal(expectedResults, result);

        var activity = Assert.Single(activities);

        Assert.Equal("vectorized_search testcollection", activity.DisplayName);
        Assert.Equal("vectorized_search", activity.GetTagItem("db.operation.name"));
        Assert.Equal("testdb", activity.GetTagItem("db.namespace"));
        Assert.Equal("testcollection", activity.GetTagItem("db.collection.name"));
        Assert.Equal("testvectorstore", activity.GetTagItem("db.system.name"));
    }
}
