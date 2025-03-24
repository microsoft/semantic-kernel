// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Moq;
using Xunit;

namespace VectorData.UnitTests.VectorSearch;

public class DelegatingVectorizedSearchTests
{
    private readonly Mock<IVectorizedSearch<string>> _mockInnerSearch;
    private readonly FakeVectorizedSearch<string> _delegatingSearch;

    public DelegatingVectorizedSearchTests()
    {
        this._mockInnerSearch = new Mock<IVectorizedSearch<string>>();
        this._delegatingSearch = new FakeVectorizedSearch<string>(this._mockInnerSearch.Object);
    }

    [Fact]
    public void ConstructorWithNullInnerSearchThrowsArgumentNullException()
    {
        Assert.Throws<ArgumentNullException>(() => new FakeVectorizedSearch<object>(null!));
    }

    [Fact]
    public async Task VectorizedSearchCallsInnerSearchAsync()
    {
        var vector = new float[] { 1.0f, 2.0f };
        var options = new VectorSearchOptions<string>();
        var searchResults = new[] { new VectorSearchResult<string>("result", 0.9f) }.ToAsyncEnumerable();
        var results = new VectorSearchResults<string>(searchResults);

        this._mockInnerSearch.Setup(s => s.VectorizedSearchAsync(vector, options, default))
                   .ReturnsAsync(results);

        var result = await this._delegatingSearch.VectorizedSearchAsync(vector, options);

        Assert.Equal(results, result);
        this._mockInnerSearch.Verify(x => x.VectorizedSearchAsync(vector, options, default), Times.Once);
    }

    private sealed class FakeVectorizedSearch<TRecord> : DelegatingVectorizedSearch<TRecord>
    {
        public FakeVectorizedSearch(IVectorizedSearch<TRecord> innerSearch) : base(innerSearch) { }
    }
}
