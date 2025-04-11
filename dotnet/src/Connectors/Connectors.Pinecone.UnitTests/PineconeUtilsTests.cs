// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.Pinecone;
using Xunit;

namespace SemanticKernel.Connectors.Pinecone.UnitTests;

[Obsolete("The IMemoryStore abstraction is being obsoleted")]
public class PineconeUtilsTests
{
    [Fact]
    public async Task EnsureValidMetadataAsyncShouldSplitMetadataWhenExceedsMaxSizeAsync()
    {
        // Arrange
        var document = new PineconeDocument
        {
            Id = "1",
            Metadata = new Dictionary<string, object> { { "text", new string('a', PineconeUtils.MaxMetadataSize + 1) } },
            Values = Array.Empty<float>()
        };

        var documents = new List<PineconeDocument> { document }.ToAsyncEnumerable();

        // Act
        var result = await PineconeUtils.EnsureValidMetadataAsync(documents).ToListAsync();

        // Assert
        Assert.True(result.Count > 1);
        Assert.All(result, item => Assert.StartsWith(document.Id, item.Id, StringComparison.Ordinal));
        Assert.All(result, item => Assert.True(Encoding.UTF8.GetByteCount(item.Metadata?["text"].ToString() ?? string.Empty) <= PineconeUtils.MaxMetadataSize));
    }

    [Fact]
    public async Task EnsureValidMetadataAsyncShouldNotSplitMetadataWhenNotExceedsMaxSizeAsync()
    {
        // Arrange
        var document = new PineconeDocument
        {
            Id = "1",
            Metadata = new Dictionary<string, object> { { "text", new string('a', PineconeUtils.MaxMetadataSize - 15) } },
            Values = Array.Empty<float>()
        };

        var documents = new List<PineconeDocument> { document }.ToAsyncEnumerable();

        // Act
        var result = await PineconeUtils.EnsureValidMetadataAsync(documents).ToListAsync();

        // Assert
        Assert.Single((IEnumerable)result);
        Assert.Equal(document.Id, result[0].Id);
        Assert.Equal(document.Metadata["text"], result[0].Metadata?["text"]);
    }

    [Fact]
    public void ConvertFilterToPineconeFilterShouldConvertFilterCorrectly()
    {
        // Arrange
        var filter = new Dictionary<string, object>
        {
            { "key1", new PineconeUtils.PineconeOperator("$eq", "value1") },
            { "key2", new List<int> { 1, 2, 3 } },
            { "key3", new DateTimeOffset(2023, 1, 1, 0, 0, 0, TimeSpan.Zero) },
            { "key4", "value4" }
        };

        // Act
        var result = PineconeUtils.ConvertFilterToPineconeFilter(filter);

        // Assert
        Assert.Equal(new Dictionary<string, object>
        {
            { "key1", new Dictionary<string, object> { { "$eq", "value1" } } },
            { "key2", new Dictionary<string, object> { { "$in", new List<int> { 1, 2, 3 } } } },
            { "key3", new Dictionary<string, object> { { "$eq", new DateTimeOffset(2023, 1, 1, 0, 0, 0, TimeSpan.Zero).ToUnixTimeSeconds() } } },
            { "key4", new Dictionary<string, object> { { "$eq", "value4" } } }
        }, result);
    }
}
