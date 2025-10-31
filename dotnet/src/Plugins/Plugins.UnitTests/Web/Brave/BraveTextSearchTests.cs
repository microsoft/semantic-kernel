// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable CS0618 // ITextSearch is obsolete
#pragma warning disable CS8602 // Dereference of a possibly null reference - for LINQ expression properties

using System;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Plugins.Web.Brave;
using Xunit;

namespace SemanticKernel.Plugins.UnitTests.Web.Brave;

public sealed class BraveTextSearchTests : IDisposable
{
    /// <summary>
    /// Initializes a new instance of the <see cref="BraveTextSearchTests"/> class.
    /// </summary>
    public BraveTextSearchTests()
    {
        this._messageHandlerStub = new MultipleHttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub, disposeHandler: false);
        this._kernel = new Kernel();
    }

    [Fact]
    public void AddBraveTextSearchSucceeds()
    {
        // Arrange
        var builder = Kernel.CreateBuilder();

        // Act
        builder.AddBraveTextSearch(apiKey: "ApiKey");
        var kernel = builder.Build();

        // Assert
        Assert.IsType<BraveTextSearch>(kernel.Services.GetRequiredService<ITextSearch>());
    }

    [Fact]
    public async Task SearchReturnsSuccessfullyAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSkResponseJson));

        // Create an ITextSearch instance using Brave search
        var textSearch = new BraveTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act
        KernelSearchResults<string> result = await textSearch.SearchAsync("What is the Semantic Kernel?", new() { Top = 10, Skip = 0 });

        // Assert
        Assert.NotNull(result);
        Assert.NotNull(result.Results);
        var resultList = await result.Results.ToListAsync();
        Assert.NotNull(resultList);
        Assert.Equal(10, resultList.Count);
        foreach (var stringResult in resultList)
        {
            Assert.NotEmpty(stringResult);
        }
    }

    [Fact]
    public async Task GetTextSearchResultsReturnsSuccessfullyAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSkResponseJson));

        // Create an ITextSearch instance using Brave search
        var textSearch = new BraveTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act
        KernelSearchResults<TextSearchResult> result = await textSearch.GetTextSearchResultsAsync("What is the Semantic Kernel?", new() { Top = 10, Skip = 0 });

        // Assert
        Assert.NotNull(result);
        Assert.NotNull(result.Results);
        var resultList = await result.Results.ToListAsync();
        Assert.NotNull(resultList);
        Assert.Equal(10, resultList.Count);
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
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSkResponseJson));

        // Create an ITextSearch instance using Brave search
        var textSearch = new BraveTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act
        KernelSearchResults<object> result = await textSearch.GetSearchResultsAsync("What is the Semantic Kernel?", new() { Top = 10, Skip = 0 });

        // Assert
        Assert.NotNull(result);
        Assert.NotNull(result.Results);
        var resultList = await result.Results.ToListAsync();
        Assert.NotNull(resultList);
        Assert.Equal(10, resultList.Count);
        foreach (BraveWebResult webPage in resultList)
        {
            Assert.NotNull(webPage.Title);
            Assert.NotNull(webPage.Description);
            Assert.NotNull(webPage.Url);
        }
    }

    [Fact]
    public async Task SearchWithCustomStringMapperReturnsSuccessfullyAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSkResponseJson));

        // Create an ITextSearch instance using Brave search
        var textSearch = new BraveTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient, StringMapper = new TestTextSearchStringMapper() });

        // Act
        KernelSearchResults<string> result = await textSearch.SearchAsync("What is the Semantic Kernel?", new() { Top = 10, Skip = 0 });

        // Assert
        Assert.NotNull(result);
        Assert.NotNull(result.Results);
        var resultList = await result.Results.ToListAsync();
        Assert.NotNull(resultList);
        Assert.Equal(10, resultList.Count);
        foreach (var stringResult in resultList)
        {
            Assert.NotEmpty(stringResult);
            var webPage = JsonSerializer.Deserialize<BraveWebResult>(stringResult);
            Assert.NotNull(webPage);
        }
    }

    [Fact]
    public async Task GetTextSearchResultsWithCustomResultMapperReturnsSuccessfullyAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSkResponseJson));

        // Create an ITextSearch instance using Brave search
        var textSearch = new BraveTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient, ResultMapper = new TestTextSearchResultMapper() });

        // Act
        KernelSearchResults<TextSearchResult> result = await textSearch.GetTextSearchResultsAsync("What is the Semantic Kernel?", new() { Top = 10, Skip = 0 });

        // Assert
        Assert.NotNull(result);
        Assert.NotNull(result.Results);
        var resultList = await result.Results.ToListAsync();
        Assert.NotNull(resultList);
        Assert.Equal(10, resultList.Count);
        foreach (var textSearchResult in resultList)
        {
            Assert.NotNull(textSearchResult);
            Assert.Equal(textSearchResult.Name, textSearchResult.Name?.ToUpperInvariant());
            Assert.Equal(textSearchResult.Value, textSearchResult.Value?.ToUpperInvariant());
            Assert.Equal(textSearchResult.Link, textSearchResult.Link?.ToUpperInvariant());
        }
    }

    //https://api.search.brave.com/res/v1/web/search?q=What%20is%20the%20Semantic%20Kernel%3F&count=5&offset=0&&country=US&search_lang=en&ui_lang=en-US&safesearch=moderate&text_decorations=True&spellcheck=False&result_filter=web&units=imperial&extra_snippets=True

    [Theory]
    [InlineData("country", "US", "https://api.search.brave.com/res/v1/web/search?q=What%20is%20the%20Semantic%20Kernel%3F&count=5&offset=0&country=US")]
    [InlineData("search_lang", "en", "https://api.search.brave.com/res/v1/web/search?q=What%20is%20the%20Semantic%20Kernel%3F&count=5&offset=0&search_lang=en")]
    [InlineData("ui_lang", "en-US", "https://api.search.brave.com/res/v1/web/search?q=What%20is%20the%20Semantic%20Kernel%3F&count=5&offset=0&ui_lang=en-US")]
    [InlineData("safesearch", "off", "https://api.search.brave.com/res/v1/web/search?q=What%20is%20the%20Semantic%20Kernel%3F&count=5&offset=0&safesearch=off")]
    [InlineData("safesearch", "moderate", "https://api.search.brave.com/res/v1/web/search?q=What%20is%20the%20Semantic%20Kernel%3F&count=5&offset=0&safesearch=moderate")]
    [InlineData("safesearch", "strict", "https://api.search.brave.com/res/v1/web/search?q=What%20is%20the%20Semantic%20Kernel%3F&count=5&offset=0&safesearch=strict")]
    [InlineData("text_decorations", true, "https://api.search.brave.com/res/v1/web/search?q=What%20is%20the%20Semantic%20Kernel%3F&count=5&offset=0&text_decorations=True")]
    [InlineData("spellcheck", false, "https://api.search.brave.com/res/v1/web/search?q=What%20is%20the%20Semantic%20Kernel%3F&count=5&offset=0&spellcheck=False")]
    [InlineData("result_filter", "web", "https://api.search.brave.com/res/v1/web/search?q=What%20is%20the%20Semantic%20Kernel%3F&count=5&offset=0&result_filter=web")]
    [InlineData("units", "imperial", "https://api.search.brave.com/res/v1/web/search?q=What%20is%20the%20Semantic%20Kernel%3F&count=5&offset=0&units=imperial")]
    [InlineData("extra_snippets", true, "https://api.search.brave.com/res/v1/web/search?q=What%20is%20the%20Semantic%20Kernel%3F&count=5&offset=0&extra_snippets=True")]
    public async Task BuildsCorrectUriForEqualityFilterAsync(string paramName, object paramValue, string requestLink)
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(SiteFilterSkResponseJson));

        // Create an ITextSearch instance using Brave search
        var textSearch = new BraveTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act
        TextSearchOptions searchOptions = new() { Top = 5, Skip = 0, Filter = new TextSearchFilter().Equality(paramName, paramValue) };
        KernelSearchResults<object> result = await textSearch.GetSearchResultsAsync("What is the Semantic Kernel?", searchOptions);

        // Assert
        var requestUris = this._messageHandlerStub.RequestUris;
        Assert.Single(requestUris);
        Assert.NotNull(requestUris[0]);
        Assert.Equal(requestLink, requestUris[0]!.AbsoluteUri);
    }

    [Fact]
    public async Task DoesNotBuildsUriForInvalidQueryParameterAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(SiteFilterSkResponseJson));
        TextSearchOptions searchOptions = new() { Top = 5, Skip = 0, Filter = new TextSearchFilter().Equality("fooBar", "Baz") };

        // Create an ITextSearch instance using Brave search
        var textSearch = new BraveTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act && Assert
        var e = await Assert.ThrowsAsync<ArgumentException>(async () => await textSearch.GetSearchResultsAsync("What is the Semantic Kernel?", searchOptions));
        Assert.Equal("Unknown equality filter clause field name 'fooBar', must be one of country,search_lang,ui_lang,safesearch,text_decorations,spellcheck,result_filter,units,extra_snippets (Parameter 'searchOptions')", e.Message);
    }

    [Fact]
    public async Task DoesNotBuildsUriForQueryParameterNullInputAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(SiteFilterSkResponseJson));
        TextSearchOptions searchOptions = new() { Top = 5, Skip = 0, Filter = new TextSearchFilter().Equality("country", null!) };

        // Create an ITextSearch instance using Brave search
        var textSearch = new BraveTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act && Assert
        var e = await Assert.ThrowsAsync<ArgumentException>(async () => await textSearch.GetSearchResultsAsync("What is the Semantic Kernel?", searchOptions));
        Assert.Equal("Unknown equality filter clause field name 'country', must be one of country,search_lang,ui_lang,safesearch,text_decorations,spellcheck,result_filter,units,extra_snippets (Parameter 'searchOptions')", e.Message);
    }

    /// <inheritdoc/>
    public void Dispose()
    {
        this._messageHandlerStub.Dispose();
        this._httpClient.Dispose();

        GC.SuppressFinalize(this);
    }

    #region Generic ITextSearch<BraveWebPage> Interface Tests

    [Fact]
    public async Task GenericSearchAsyncReturnsResultsSuccessfullyAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSkResponseJson));
        ITextSearch<BraveWebPage> textSearch = new BraveTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act
        var searchOptions = new TextSearchOptions<BraveWebPage>
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
        var requestUris = this._messageHandlerStub.RequestUris;
        Assert.Single(requestUris);
        Assert.NotNull(requestUris[0]);
        Assert.Contains("count=4", requestUris[0].AbsoluteUri);
    }

    [Fact]
    public async Task GenericGetSearchResultsAsyncReturnsResultsSuccessfullyAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSkResponseJson));
        ITextSearch<BraveWebPage> textSearch = new BraveTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act
        var searchOptions = new TextSearchOptions<BraveWebPage>
        {
            Top = 3,
            Skip = 0
        };
        KernelSearchResults<object> result = await textSearch.GetSearchResultsAsync("What is the Semantic Kernel?", searchOptions);

        // Assert - Verify generic interface returns results
        Assert.NotNull(result);
        Assert.NotNull(result.Results);
        var resultList = await result.Results.ToListAsync();
        Assert.NotEmpty(resultList);
        // Results are still objects (BraveSearchResult) not BraveWebPage since that's just for filtering

        // Verify the request was made correctly
        var requestUris = this._messageHandlerStub.RequestUris;
        Assert.Single(requestUris);
        Assert.NotNull(requestUris[0]);
        Assert.Contains("count=3", requestUris[0].AbsoluteUri);
    }

    [Fact]
    public async Task GenericGetTextSearchResultsAsyncReturnsResultsSuccessfullyAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSkResponseJson));
        ITextSearch<BraveWebPage> textSearch = new BraveTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act
        var searchOptions = new TextSearchOptions<BraveWebPage>
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
        var requestUris = this._messageHandlerStub.RequestUris;
        Assert.Single(requestUris);
        Assert.NotNull(requestUris[0]);
        Assert.Contains("count=5", requestUris[0].AbsoluteUri);
    }

    [Fact]
    public async Task CollectionContainsFilterThrowsNotSupportedExceptionAsync()
    {
        // Arrange - Tests both Enumerable.Contains (C# 13-) and MemoryExtensions.Contains (C# 14+)
        // The same code array.Contains() resolves differently based on C# language version:
        // - C# 13 and earlier: Enumerable.Contains (LINQ extension method)
        // - C# 14 and later: MemoryExtensions.Contains (span-based optimization due to "first-class spans")
        // Our implementation handles both identically since Brave API has limited query operators
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSkResponseJson));
        ITextSearch<BraveWebPage> textSearch = new BraveTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });
        string[] sites = ["microsoft.com", "github.com"];

        // Act & Assert - Verify that collection Contains pattern throws clear exception
        var searchOptions = new TextSearchOptions<BraveWebPage>
        {
            Top = 5,
            Skip = 0,
            Filter = page => sites.Contains(page.Url!.ToString())  // Enumerable.Contains (C# 13-) or MemoryExtensions.Contains (C# 14+)
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
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSkResponseJson));
        ITextSearch<BraveWebPage> textSearch = new BraveTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act - String.Contains should continue to work
        var searchOptions = new TextSearchOptions<BraveWebPage>
        {
            Top = 5,
            Skip = 0,
            Filter = page => page.Title.Contains("Kernel")  // String.Contains - instance method
        };
        KernelSearchResults<string> result = await textSearch.SearchAsync("Semantic Kernel tutorial", searchOptions);

        // Assert - Verify String.Contains works correctly
        var requestUris = this._messageHandlerStub.RequestUris;
        Assert.Single(requestUris);
        Assert.NotNull(requestUris[0]);
        Assert.Contains("Kernel", requestUris[0].AbsoluteUri);
        Assert.Contains("count=5", requestUris[0].AbsoluteUri);
    }

    #endregion

    #region private
    private const string WhatIsTheSkResponseJson = "./TestData/brave_what_is_the_semantic_kernel.json";
    private const string SiteFilterSkResponseJson = "./TestData/brave_site_filter_what_is_the_semantic_kernel.json";

    private readonly MultipleHttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;
    private readonly Kernel _kernel;

    /// <summary>
    /// Test mapper which converts a BraveWebPage search result to a string using JSON serialization.
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
    /// Test mapper which converts a BraveWebPage search result to a string using JSON serialization.
    /// </summary>
    private sealed class TestTextSearchResultMapper : ITextSearchResultMapper
    {
        /// <inheritdoc />
        public TextSearchResult MapFromResultToTextSearchResult(object result)
        {
            if (result is not BraveWebResult webPage)
            {
                throw new ArgumentException("Result must be a BraveWebPage", nameof(result));
            }

            return new TextSearchResult(webPage.Description?.ToUpperInvariant() ?? string.Empty)
            {
                Name = webPage.Title?.ToUpperInvariant(),
                Link = webPage.Url?.ToUpperInvariant(),
            };
        }
    }
    #endregion
}
