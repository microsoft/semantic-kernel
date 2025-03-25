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

namespace VectorData.UnitTests.VectorStorage;

public class OpenTelemetryVectorStoreTests
{
    [Fact]
    public async Task ListCollectionNamesWorksWithActivityAsync()
    {
        // Arrange
        var sourceName = Guid.NewGuid().ToString();

        string[] colletions = ["col1", "col2"];
        var mockInnerStore = new Mock<IVectorStore>();

        mockInnerStore.Setup(s => s.ListCollectionNamesAsync(default))
                  .Returns(colletions.ToAsyncEnumerable());

        mockInnerStore.Setup(s => s.GetService(typeof(VectorStoreMetadata), It.IsAny<object?>()))
                  .Returns(new VectorStoreMetadata
                  {
                      VectorStoreSystemName = "testvectorstore",
                      DatabaseName = "testdb"
                  });

        var vectorStore = mockInnerStore.Object
            .AsBuilder()
            .UseOpenTelemetry(sourceName)
            .Build();

        var activities = new List<Activity>();
        using var tracerProvider = OpenTelemetry.Sdk.CreateTracerProviderBuilder()
            .AddSource(sourceName)
            .AddInMemoryExporter(activities)
            .Build();

        // Act
        var result = await vectorStore.ListCollectionNamesAsync().ToListAsync();

        // Assert
        Assert.Equal(colletions, result);

        var activity = Assert.Single(activities);

        Assert.Equal("list_collection_names testdb", activity.DisplayName);
        Assert.Equal("list_collection_names", activity.GetTagItem("db.operation.name"));
        Assert.Equal("testdb", activity.GetTagItem("db.namespace"));
        Assert.Equal("testvectorstore", activity.GetTagItem("db.system.name"));
    }
}
