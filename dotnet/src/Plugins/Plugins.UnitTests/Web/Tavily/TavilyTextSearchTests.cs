// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable CS0618 // ITextSearch is obsolete
#pragma warning disable CS8602 // Dereference of a possibly null reference - for LINQ expression properties

using System;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Plugins.Web.Tavily;
using Xunit;

namespace SemanticKernel.Plugins.UnitTests.Web.Tavily;

public sealed class TavilyTextSearchTests : IDisposable
{
    /// <summary>
    /// Initializes a new instance of the <see cref="TavilyTextSearchTests"/> class.
    /// </summary>
    public TavilyTextSearchTests()
    {
        this._messageHandlerStub = new MultipleHttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub, disposeHandler: false);
        this._kernel = new Kernel();
    }

    [Fact]
    public void AddTavilyTextSearchSucceeds()
    {
        // Arrange
        var builder = Kernel.CreateBuilder();

        // Act
        builder.AddTavilyTextSearch(apiKey: "ApiKey");
        var kernel = builder.Build();

        // Assert
        Assert.IsType<TavilyTextSearch>(kernel.Services.GetRequiredService<ITextSearch>());
    }

    [Fact]
    public async Task SearchReturnsSuccessfullyAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));

        // Create an ITextSearch instance using Tavily search
        var textSearch = new TavilyTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act
        KernelSearchResults<string> result = await textSearch.SearchAsync("What is the Semantic Kernel?", new() { Top = 4, Skip = 0 });

        // Assert
        Assert.NotNull(result);
        Assert.NotNull(result.Results);
        var resultList = await result.Results.ToListAsync();
        Assert.NotNull(resultList);
        Assert.Equal(4, resultList.Count);
        foreach (var stringResult in resultList)
        {
            Assert.NotEmpty(stringResult);
        }
    }

    [Fact]
    public async Task GetTextSearchResultsReturnsSuccessfullyAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));

        // Create an ITextSearch instance using Tavily search
        var textSearch = new TavilyTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act
        KernelSearchResults<TextSearchResult> result = await textSearch.GetTextSearchResultsAsync("What is the Semantic Kernel?", new() { Top = 4, Skip = 0 });

        // Assert
        Assert.NotNull(result);
        Assert.NotNull(result.Results);
        var resultList = await result.Results.ToListAsync();
        Assert.NotNull(resultList);
        Assert.Equal(4, resultList.Count);
        foreach (var textSearchResult in resultList)
        {
            Assert.NotNull(textSearchResult.Name);
            Assert.NotNull(textSearchResult.Value);
            Assert.NotNull(textSearchResult.Link);
        }
    }

    [Fact]
    public async Task GetSearchResultsReturnsSuccessfullyAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));

        // Create an ITextSearch instance using Tavily search
        var textSearch = new TavilyTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient, IncludeRawContent = true });

        // Act
        KernelSearchResults<object> result = await textSearch.GetSearchResultsAsync("What is the Semantic Kernel?", new() { Top = 4, Skip = 0 });

        // Assert
        Assert.NotNull(result);
        Assert.NotNull(result.Results);
        var resultList = await result.Results.ToListAsync();
        Assert.NotNull(resultList);
        Assert.Equal(4, resultList.Count);
        foreach (TavilySearchResult searchResult in resultList)
        {
            Assert.NotNull(searchResult.Title);
            Assert.NotNull(searchResult.Url);
            Assert.NotNull(searchResult.Content);
            Assert.NotNull(searchResult.RawContent);
            Assert.True(searchResult.Score > 0);
        }
    }

    [Fact]
    public async Task SearchWithCustomStringMapperReturnsSuccessfullyAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));

        // Create an ITextSearch instance using Tavily search
        var textSearch = new TavilyTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient, StringMapper = new TestTextSearchStringMapper() });

        // Act
        KernelSearchResults<string> result = await textSearch.SearchAsync("What is the Semantic Kernel?", new() { Top = 4, Skip = 0 });

        // Assert
        Assert.NotNull(result);
        Assert.NotNull(result.Results);
        var resultList = await result.Results.ToListAsync();
        Assert.NotNull(resultList);
        Assert.Equal(4, resultList.Count);
        foreach (var stringResult in resultList)
        {
            Assert.NotEmpty(stringResult);
            var searchResult = JsonSerializer.Deserialize<TavilySearchResult>(stringResult);
            Assert.NotNull(searchResult);
        }
    }

    [Fact]
    public async Task GetTextSearchResultsWithCustomResultMapperReturnsSuccessfullyAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));

        // Create an ITextSearch instance using Tavily search
        var textSearch = new TavilyTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient, ResultMapper = new TestTextSearchResultMapper() });

        // Act
        KernelSearchResults<TextSearchResult> result = await textSearch.GetTextSearchResultsAsync("What is the Semantic Kernel?", new() { Top = 4, Skip = 0 });

        // Assert
        Assert.NotNull(result);
        Assert.NotNull(result.Results);
        var resultList = await result.Results.ToListAsync();
        Assert.NotNull(resultList);
        Assert.Equal(4, resultList.Count);
        foreach (var textSearchResult in resultList)
        {
            Assert.NotNull(textSearchResult);
            Assert.Equal(textSearchResult.Name, textSearchResult.Name?.ToUpperInvariant());
            Assert.Equal(textSearchResult.Value, textSearchResult.Value?.ToUpperInvariant());
            Assert.Equal(textSearchResult.Link, textSearchResult.Link?.ToUpperInvariant());
        }
    }

    [Fact]
    public async Task SearchWithAnswerReturnsSuccessfullyAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));

        // Create an ITextSearch instance using Tavily search
        var textSearch = new TavilyTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient, IncludeAnswer = true });

        // Act
        KernelSearchResults<string> result = await textSearch.SearchAsync("What is the Semantic Kernel?", new() { Top = 4, Skip = 0 });

        // Assert
        Assert.NotNull(result);
        Assert.NotNull(result.Results);
        var resultList = await result.Results.ToListAsync();
        Assert.NotNull(resultList);
        Assert.Equal(5, resultList.Count);
        foreach (var stringResult in resultList)
        {
            Assert.NotEmpty(stringResult);
        }
    }

    [Fact]
    public async Task SearchWithImagesReturnsSuccessfullyAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));

        // Create an ITextSearch instance using Tavily search
        var textSearch = new TavilyTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient, IncludeImages = true });

        // Act
        KernelSearchResults<string> result = await textSearch.SearchAsync("What is the Semantic Kernel?", new() { Top = 4, Skip = 0 });

        // Assert
        Assert.NotNull(result);
        Assert.NotNull(result.Results);
        var resultList = await result.Results.ToListAsync();
        Assert.NotNull(resultList);
        Assert.Equal(9, resultList.Count);
        foreach (var stringResult in resultList)
        {
            Assert.NotEmpty(stringResult);
        }
    }

    [Fact]
    public async Task GetTextSearchResultsWithAnswerReturnsSuccessfullyAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));

        // Create an ITextSearch instance using Tavily search
        var textSearch = new TavilyTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient, IncludeAnswer = true });

        // Act
        KernelSearchResults<TextSearchResult> result = await textSearch.GetTextSearchResultsAsync("What is the Semantic Kernel?", new() { Top = 4, Skip = 0 });

        // Assert
        Assert.NotNull(result);
        Assert.NotNull(result.Results);
        var resultList = await result.Results.ToListAsync();
        Assert.NotNull(resultList);
        Assert.Equal(4, resultList.Count);
        foreach (var textSearchResult in resultList)
        {
            Assert.NotNull(textSearchResult.Name);
            Assert.NotNull(textSearchResult.Value);
            Assert.NotNull(textSearchResult.Link);
        }
    }

    [Fact]
    public async Task GetTextSearchResultsWithImagesReturnsSuccessfullyAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));

        // Create an ITextSearch instance using Tavily search
        var textSearch = new TavilyTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient, IncludeImages = true, IncludeImageDescriptions = true });

        // Act
        KernelSearchResults<TextSearchResult> result = await textSearch.GetTextSearchResultsAsync("What is the Semantic Kernel?", new() { Top = 4, Skip = 0 });

        // Assert
        Assert.NotNull(result);
        Assert.NotNull(result.Results);
        var resultList = await result.Results.ToListAsync();
        Assert.NotNull(resultList);
        Assert.Equal(9, resultList.Count);
        foreach (var textSearchResult in resultList)
        {
            Assert.NotNull(textSearchResult.Name);
            Assert.NotNull(textSearchResult.Value);
            Assert.NotNull(textSearchResult.Link);
        }
    }

    [Theory]
    [InlineData("topic", "general", "{\"query\":\"What is the Semantic Kernel?\",\"topic\":\"general\",\"max_results\":4}")]
    [InlineData("topic", "news", "{\"query\":\"What is the Semantic Kernel?\",\"topic\":\"news\",\"max_results\":4}")]
    [InlineData("time_range", "day", "{\"query\":\"What is the Semantic Kernel?\",\"max_results\":4,\"time_range\":\"day\"}")]
    [InlineData("time_range", "week", "{\"query\":\"What is the Semantic Kernel?\",\"max_results\":4,\"time_range\":\"week\"}")]
    [InlineData("time_range", "month", "{\"query\":\"What is the Semantic Kernel?\",\"max_results\":4,\"time_range\":\"month\"}")]
    [InlineData("time_range", "year", "{\"query\":\"What is the Semantic Kernel?\",\"max_results\":4,\"time_range\":\"year\"}")]
    [InlineData("time_range", "d", "{\"query\":\"What is the Semantic Kernel?\",\"max_results\":4,\"time_range\":\"d\"}")]
    [InlineData("time_range", "w", "{\"query\":\"What is the Semantic Kernel?\",\"max_results\":4,\"time_range\":\"w\"}")]
    [InlineData("time_range", "m", "{\"query\":\"What is the Semantic Kernel?\",\"max_results\":4,\"time_range\":\"m\"}")]
    [InlineData("time_range", "y", "{\"query\":\"What is the Semantic Kernel?\",\"max_results\":4,\"time_range\":\"y\"}")]
    [InlineData("days", 5, "{\"query\":\"What is the Semantic Kernel?\",\"max_results\":4,\"days\":5}")]
    [InlineData("include_domain", "devblogs.microsoft.com", "{\"query\":\"What is the Semantic Kernel?\",\"max_results\":4,\"include_domains\":[\"devblogs.microsoft.com\"]}")]
    [InlineData("exclude_domain", "devblogs.microsoft.com", "{\"query\":\"What is the Semantic Kernel?\",\"max_results\":4,\"exclude_domains\":[\"devblogs.microsoft.com\"]}")]
    public async Task BuildsCorrectRequestForEqualityFilterAsync(string paramName, object paramValue, string request)
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(SiteFilterDevBlogsResponseJson));

        // Create an ITextSearch instance using Tavily search
        var textSearch = new TavilyTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act
        TextSearchOptions searchOptions = new() { Top = 4, Skip = 0, Filter = new TextSearchFilter().Equality(paramName, paramValue) };
        KernelSearchResults<object> result = await textSearch.GetSearchResultsAsync("What is the Semantic Kernel?", searchOptions);

        // Assert
        var requestContents = this._messageHandlerStub.RequestContents;
        Assert.Single(requestContents);
        Assert.NotNull(requestContents[0]);
        var actualRequest = Encoding.UTF8.GetString(requestContents[0]!);
        Assert.Equal(request, Encoding.UTF8.GetString(requestContents[0]!));
    }

    [Theory]
    [InlineData("fooBar", "baz")]
    public async Task DoesNotBuildRequestForInvalidQueryParameterAsync(string paramName, object paramValue)
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(SiteFilterDevBlogsResponseJson));
        TextSearchOptions searchOptions = new() { Top = 4, Skip = 0, Filter = new TextSearchFilter().Equality(paramName, paramValue) };

        // Create an ITextSearch instance using Tavily search
        var textSearch = new TavilyTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act && Assert
        var e = await Assert.ThrowsAsync<ArgumentException>(async () => await textSearch.GetSearchResultsAsync("What is the Semantic Kernel?", searchOptions));
        Assert.Equal("Unknown equality filter clause field name 'fooBar', must be one of topic,time_range,days,include_domain,exclude_domain (Parameter 'searchOptions')", e.Message);
    }

    [Fact]
    public async Task DoesNotBuildRequestForInvalidQueryAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(SiteFilterDevBlogsResponseJson));

        // Create an ITextSearch instance using Tavily search
        var textSearch = new TavilyTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act && Assert
        var e = await Assert.ThrowsAsync<ArgumentNullException>(async () => await textSearch.GetSearchResultsAsync(null!));
        Assert.Equal("Value cannot be null. (Parameter 'query')", e.Message);
    }

    /// <inheritdoc/>
    public void Dispose()
    {
        this._messageHandlerStub.Dispose();
        this._httpClient.Dispose();
        GC.SuppressFinalize(this);
    }

    #region Generic ITextSearch<TavilyWebPage> Interface Tests

    [Fact]
    public async Task GenericSearchAsyncReturnsResultsSuccessfullyAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(SiteFilterDevBlogsResponseJson));
        ITextSearch<TavilyWebPage> textSearch = new TavilyTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act
        var searchOptions = new TextSearchOptions<TavilyWebPage>
        {
            Top = 4,
            Skip = 0
        };
        KernelSearchResults<string> result = await textSearch.SearchAsync("What is the Semantic Kernel?", searchOptions);

        // Assert - Verify basic generic interface functionality
        Assert.NotNull(result);
        Assert.NotNull(result.Results);
        var resultList = await result.Results.ToListAsync();
        Assert.NotEmpty(resultList);

        // Verify the request was made correctly
        var requestContents = this._messageHandlerStub.RequestContents;
        Assert.Single(requestContents);
        Assert.NotNull(requestContents[0]);
        var requestBodyJson = Encoding.UTF8.GetString(requestContents[0]!);
        Assert.Contains("\"query\"", requestBodyJson);
        Assert.Contains("\"max_results\":4", requestBodyJson);
    }

    [Fact]
    public async Task GenericGetSearchResultsAsyncReturnsResultsSuccessfullyAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(SiteFilterDevBlogsResponseJson));
        ITextSearch<TavilyWebPage> textSearch = new TavilyTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act
        var searchOptions = new TextSearchOptions<TavilyWebPage>
        {
            Top = 3,
            Skip = 0
        };
        KernelSearchResults<TavilyWebPage> result = await textSearch.GetSearchResultsAsync("What is the Semantic Kernel?", searchOptions);

        // Assert - Verify generic interface returns results
        Assert.NotNull(result);
        Assert.NotNull(result.Results);
        var resultList = await result.Results.ToListAsync();
        Assert.NotEmpty(resultList);
        // Results are now strongly typed as TavilyWebPage

        // Verify the request was made correctly
        var requestContents = this._messageHandlerStub.RequestContents;
        Assert.Single(requestContents);
        Assert.NotNull(requestContents[0]);
        var requestBodyJson = Encoding.UTF8.GetString(requestContents[0]!);
        Assert.Contains("\"max_results\":3", requestBodyJson);
    }

    [Fact]
    public async Task GenericGetTextSearchResultsAsyncReturnsResultsSuccessfullyAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(SiteFilterDevBlogsResponseJson));
        ITextSearch<TavilyWebPage> textSearch = new TavilyTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act
        var searchOptions = new TextSearchOptions<TavilyWebPage>
        {
            Top = 5,
            Skip = 0
        };
        KernelSearchResults<TextSearchResult> result = await textSearch.GetTextSearchResultsAsync("What is the Semantic Kernel?", searchOptions);

        // Assert - Verify generic interface returns TextSearchResult objects
        Assert.NotNull(result);
        Assert.NotNull(result.Results);
        var resultList = await result.Results.ToListAsync();
        Assert.NotEmpty(resultList);
        Assert.All(resultList, item => Assert.IsType<TextSearchResult>(item));

        // Verify the request was made correctly
        var requestContents = this._messageHandlerStub.RequestContents;
        Assert.Single(requestContents);
        Assert.NotNull(requestContents[0]);
        var requestBodyJson = Encoding.UTF8.GetString(requestContents[0]!);
        Assert.Contains("\"max_results\":5", requestBodyJson);
    }

    [Fact]
    public async Task CollectionContainsFilterThrowsNotSupportedExceptionAsync()
    {
        // Arrange - Tests both Enumerable.Contains (C# 13-) and MemoryExtensions.Contains (C# 14+)
        // The same code array.Contains() resolves differently based on C# language version:
        // - C# 13 and earlier: Enumerable.Contains (LINQ extension method)
        // - C# 14 and later: MemoryExtensions.Contains (span-based optimization due to "first-class spans")
        // Our implementation handles both identically since Tavily API has limited query operators
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(SiteFilterDevBlogsResponseJson));
        ITextSearch<TavilyWebPage> textSearch = new TavilyTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });
        string[] domains = ["microsoft.com", "github.com"];

        // Act & Assert - Verify that collection Contains pattern throws clear exception
        var searchOptions = new TextSearchOptions<TavilyWebPage>
        {
            Top = 5,
            Skip = 0,
            Filter = page => domains.Contains(page.Url!.ToString())  // Enumerable.Contains (C# 13-) or MemoryExtensions.Contains (C# 14+)
        };

        var exception = await Assert.ThrowsAsync<NotSupportedException>(async () =>
        {
            await textSearch.SearchAsync("test", searchOptions);
        });

        // Assert - Verify error message explains the limitation clearly
        Assert.Contains("Collection Contains filters", exception.Message);
        Assert.Contains("not supported", exception.Message);
    }

    [Fact]
    public async Task StringContainsStillWorksWithLINQFiltersAsync()
    {
        // Arrange - Verify that String.Contains (instance method) still works
        // String.Contains is NOT affected by C# 14 "first-class spans" - only arrays are
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(SiteFilterDevBlogsResponseJson));
        ITextSearch<TavilyWebPage> textSearch = new TavilyTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act - String.Contains should continue to work
        var searchOptions = new TextSearchOptions<TavilyWebPage>
        {
            Top = 5,
            Skip = 0,
            Filter = page => page.Title.Contains("Kernel")  // String.Contains - instance method
        };
        KernelSearchResults<string> result = await textSearch.SearchAsync("Semantic Kernel tutorial", searchOptions);

        // Assert - Verify String.Contains works correctly
        var requestContents = this._messageHandlerStub.RequestContents;
        Assert.Single(requestContents);
        Assert.NotNull(requestContents[0]);
        var requestBodyJson = Encoding.UTF8.GetString(requestContents[0]!);
        Assert.Contains("Kernel", requestBodyJson);
        Assert.Contains("\"max_results\":5", requestBodyJson);
    }

    #endregion

    #region private
    private const string WhatIsTheSKResponseJson = "./TestData/tavily_what_is_the_semantic_kernel.json";
    private const string SiteFilterDevBlogsResponseJson = "./TestData/tavily_site_filter_devblogs_microsoft.com.json";

    private readonly MultipleHttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;
    private readonly Kernel _kernel;

    /// <summary>
    /// Test mapper which converts a TavilyWebPage search result to a string using JSON serialization.
    /// </summary>
    private sealed class TestTextSearchStringMapper : ITextSearchStringMapper
    {
        /// <inheritdoc />
        public string MapFromResultToString(object result)
        {
            return JsonSerializer.Serialize(result);
        }
    }

    /// <summary>
    /// Test mapper which converts a TavilyWebPage search result to a string using JSON serialization.
    /// </summary>
    private sealed class TestTextSearchResultMapper : ITextSearchResultMapper
    {
        /// <inheritdoc />
        public TextSearchResult MapFromResultToTextSearchResult(object result)
        {
            if (result is not TavilySearchResult searchResult)
            {
                throw new ArgumentException("Result must be a TavilySearchResult", nameof(result));
            }

            return new TextSearchResult(searchResult.Content?.ToUpperInvariant() ?? string.Empty)
            {
                Name = searchResult.Title?.ToUpperInvariant(),
                Link = searchResult.Url?.ToUpperInvariant(),
            };
        }
    }
    #endregion
}
