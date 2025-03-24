// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Moq;
using Xunit;

namespace VectorData.UnitTests.VectorSearch;

public class DelegatingVectorizableTextSearchTests
{
    private readonly Mock<IVectorizableTextSearch<string>> _mockInnerSearch;
    private readonly FakeVectorizableTextSearch<string> _delegatingSearch;

    public DelegatingVectorizableTextSearchTests()
    {
        this._mockInnerSearch = new Mock<IVectorizableTextSearch<string>>();
        this._delegatingSearch = new FakeVectorizableTextSearch<string>(this._mockInnerSearch.Object);
    }

    [Fact]
    public void ConstructorWithNullInnerSearchThrowsArgumentNullException()
    {
        Assert.Throws<ArgumentNullException>(() => new FakeVectorizableTextSearch<string>(null!));
    }

    [Fact]
    public async Task VectorizableTextSearchCallsInnerSearchAsync()
    {
        var searchText = "test query";
        var options = new VectorSearchOptions<string>();
        var searchResults = new[] { new VectorSearchResult<string>("result", 0.9f) }.ToAsyncEnumerable();
        var results = new VectorSearchResults<string>(searchResults);

        this._mockInnerSearch.Setup(s => s.VectorizableTextSearchAsync(searchText, options, default))
            .ReturnsAsync(results);

        var result = await this._delegatingSearch.VectorizableTextSearchAsync(searchText, options);

        Assert.Equal(results, result);
        this._mockInnerSearch.Verify(x => x.VectorizableTextSearchAsync(searchText, options, default), Times.Once);
    }

    private sealed class FakeVectorizableTextSearch<TRecord> : DelegatingVectorizableTextSearch<TRecord>
    {
        public FakeVectorizableTextSearch(IVectorizableTextSearch<TRecord> innerSearch) : base(innerSearch) { }
    }
}
