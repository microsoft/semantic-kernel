// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Moq;
using Xunit;

namespace VectorData.UnitTests.VectorSearch;

public class DelegatingKeywordHybridSearchTests
{
    private readonly Mock<IKeywordHybridSearch<string>> _mockInnerSearch;
    private readonly FakeKeywordHybridSearch<string> _delegatingSearch;

    public DelegatingKeywordHybridSearchTests()
    {
        this._mockInnerSearch = new Mock<IKeywordHybridSearch<string>>();
        this._delegatingSearch = new FakeKeywordHybridSearch<string>(this._mockInnerSearch.Object);
    }

    [Fact]
    public void ConstructorWithNullInnerSearchThrowsArgumentNullException()
    {
        Assert.Throws<ArgumentNullException>(() => new FakeKeywordHybridSearch<string>(null!));
    }

    [Fact]
    public async Task HybridSearchCallsInnerSearchAsync()
    {
        var vector = new float[] { 1.0f, 2.0f };
        var keywords = new List<string> { "test", "search" };
        var options = new HybridSearchOptions<string>();
        var searchResults = new[] { new VectorSearchResult<string>("result", 0.9f) }.ToAsyncEnumerable();
        var results = new VectorSearchResults<string>(searchResults);

        this._mockInnerSearch.Setup(s => s.HybridSearchAsync(vector, keywords, options, default))
            .ReturnsAsync(results);

        var result = await this._delegatingSearch.HybridSearchAsync(vector, keywords, options);

        Assert.Equal(results, result);
        this._mockInnerSearch.Verify(x => x.HybridSearchAsync(vector, keywords, options, default), Times.Once);
    }

    private sealed class FakeKeywordHybridSearch<TRecord> : DelegatingKeywordHybridSearch<TRecord>
    {
        public FakeKeywordHybridSearch(IKeywordHybridSearch<TRecord> innerSearch) : base(innerSearch) { }
    }
}
