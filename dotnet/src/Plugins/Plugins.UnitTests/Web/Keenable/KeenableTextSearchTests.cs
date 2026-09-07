// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable CS0618 // ITextSearch is obsolete
#pragma warning disable CS8602 // Dereference of a possibly null reference - for LINQ expression properties

using System;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Plugins.Web.Keenable;
using Xunit;

namespace SemanticKernel.Plugins.UnitTests.Web.Keenable;

public sealed class KeenableTextSearchTests : IDisposable
{
    /// <summary>
    /// Initializes a new instance of the <see cref="KeenableTextSearchTests"/> class.
    /// </summary>
    public KeenableTextSearchTests()
    {
        this._messageHandlerStub = new MultipleHttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub, disposeHandler: false);
        this._kernel = new Kernel();
    }

    [Fact]
    public void AddKeenableTextSearchWithoutApiKeySucceeds()
    {
        // Arrange
        var builder = Kernel.CreateBuilder();

        // Act
        builder.AddKeenableTextSearch();
        var kernel = builder.Build();

        // Assert
        Assert.IsType<KeenableTextSearch>(kernel.Services.GetRequiredService<ITextSearch>());
    }

    [Fact]
    public void AddKeenableTextSearchWithApiKeySucceeds()
    {
        // Arrange
        var builder = Kernel.CreateBuilder();

        // Act
        builder.AddKeenableTextSearch(apiKey: "ApiKey");
        var kernel = builder.Build();

        // Assert
        Assert.IsType<KeenableTextSearch>(kernel.Services.GetRequiredService<ITextSearch>());
    }

    [Fact]
    public async Task SearchReturnsSuccessfullyAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));

        // Create an ITextSearch instance using Keenable search
        var textSearch = new KeenableTextSearch(options: new() { HttpClient = this._httpClient });

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

        // Create an ITextSearch instance using Keenable search
        var textSearch = new KeenableTextSearch(options: new() { HttpClient = this._httpClient });

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
            Assert.NotEmpty(textSearchResult.Value);
        }

        // The first result maps title, snippet and url to Name, Value and Link
        Assert.Equal("Semantic Kernel", resultList[0].Name);
        Assert.StartsWith("[1][9] As of June 2026", resultList[0].Value, StringComparison.Ordinal);
        Assert.Equal("https://aiwiki.ai/wiki/semantic_kernel", resultList[0].Link);
    }

    [Fact]
    public async Task GetSearchResultsReturnsSuccessfullyAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));

        // Create an ITextSearch instance using Keenable search
        var textSearch = new KeenableTextSearch(options: new() { HttpClient = this._httpClient });

        // Act
        KernelSearchResults<object> result = await textSearch.GetSearchResultsAsync("What is the Semantic Kernel?", new() { Top = 4, Skip = 0 });

        // Assert
        Assert.NotNull(result);
        Assert.NotNull(result.Results);
        var resultList = await result.Results.ToListAsync();
        Assert.NotNull(resultList);
        Assert.Equal(4, resultList.Count);
        foreach (KeenableSearchResult searchResult in resultList)
        {
            Assert.NotEmpty(searchResult.Title);
            Assert.NotEmpty(searchResult.Url);
            Assert.NotNull(searchResult.Snippet);
            Assert.NotEmpty(searchResult.Snippet);
        }

        Assert.NotNull(resultList.Cast<KeenableSearchResult>().First().PublishedAt);
    }

    [Fact]
    public async Task TextSearchResultFallsBackToDescriptionWhenSnippetIsEmptyAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse("""
            {"query":"q","results":[
              {"title":"Empty snippet","url":"https://example.com/a","description":"Description A","snippet":""},
              {"title":"No snippet","url":"https://example.com/b","description":"Description B"},
              {"title":"Has snippet","url":"https://example.com/c","description":"Description C","snippet":"Snippet C"}
            ]}
            """);
        var textSearch = new KeenableTextSearch(options: new() { HttpClient = this._httpClient });

        // Act
        KernelSearchResults<TextSearchResult> result = await textSearch.GetTextSearchResultsAsync("q", new() { Top = 3 });
        var resultList = await result.Results.ToListAsync();

        // Assert
        Assert.Equal(3, resultList.Count);
        Assert.Equal("Description A", resultList[0].Value);
        Assert.Equal("Description B", resultList[1].Value);
        Assert.Equal("Snippet C", resultList[2].Value);
    }

    [Fact]
    public async Task RequestWithoutApiKeyUsesPublicEndpointAndTitleHeaderAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));
        var textSearch = new KeenableTextSearch(options: new() { HttpClient = this._httpClient });

        // Act
        await textSearch.SearchAsync("What is the Semantic Kernel?", new() { Top = 4 });

        // Assert
        Assert.Single(this._messageHandlerStub.RequestUris);
        Assert.Equal(HttpMethod.Post, this._messageHandlerStub.Methods[0]);
        Assert.Equal("https://api.keenable.ai/v1/search/public", this._messageHandlerStub.RequestUris[0]!.AbsoluteUri);

        var headers = this._messageHandlerStub.RequestHeaders[0]!;
        Assert.Equal("semantic-kernel", headers.GetValues("X-Keenable-Title").Single());
        Assert.False(headers.Contains("X-API-Key"));

        var requestBodyJson = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContents[0]!);
        Assert.Equal("{\"query\":\"What is the Semantic Kernel?\",\"max_results\":4}", requestBodyJson);
    }

    [Theory]
    [InlineData("ApiKey")]
    [InlineData("  ApiKey  ")]
    public async Task RequestWithApiKeyUsesAuthenticatedEndpointAndApiKeyHeaderAsync(string apiKey)
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));
        var textSearch = new KeenableTextSearch(apiKey: apiKey, options: new() { HttpClient = this._httpClient });

        // Act
        await textSearch.SearchAsync("What is the Semantic Kernel?", new() { Top = 4 });

        // Assert
        Assert.Single(this._messageHandlerStub.RequestUris);
        Assert.Equal("https://api.keenable.ai/v1/search", this._messageHandlerStub.RequestUris[0]!.AbsoluteUri);

        var headers = this._messageHandlerStub.RequestHeaders[0]!;
        Assert.Equal(apiKey, headers.GetValues("X-API-Key").Single());
        Assert.Equal("semantic-kernel", headers.GetValues("X-Keenable-Title").Single());

        // The key travels in the header only, never in the body
        var requestBodyJson = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContents[0]!);
        Assert.DoesNotContain("ApiKey", requestBodyJson);
    }

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("   ")]
    public async Task EmptyApiKeyIsTreatedAsNoApiKeyAsync(string? apiKey)
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));
        var textSearch = new KeenableTextSearch(apiKey: apiKey, options: new() { HttpClient = this._httpClient });

        // Act
        await textSearch.SearchAsync("What is the Semantic Kernel?", new() { Top = 4 });

        // Assert
        Assert.Equal("https://api.keenable.ai/v1/search/public", this._messageHandlerStub.RequestUris[0]!.AbsoluteUri);
        Assert.False(this._messageHandlerStub.RequestHeaders[0]!.Contains("X-API-Key"));
    }

    [Theory]
    [InlineData("https://search.example.com", false, "https://search.example.com/v1/search/public")]
    [InlineData("https://search.example.com/", true, "https://search.example.com/v1/search")]
    [InlineData("https://search.example.com/proxy", false, "https://search.example.com/proxy/v1/search/public")]
    public async Task CustomEndpointIsUsedAsBaseAddressAsync(string endpoint, bool withApiKey, string expectedUri)
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));
        var textSearch = new KeenableTextSearch(apiKey: withApiKey ? "ApiKey" : null, options: new() { HttpClient = this._httpClient, Endpoint = new Uri(endpoint) });

        // Act
        await textSearch.SearchAsync("What is the Semantic Kernel?", new() { Top = 4 });

        // Assert
        Assert.Equal(expectedUri, this._messageHandlerStub.RequestUris[0]!.AbsoluteUri);
    }

    [Fact]
    public async Task SnippetMaxLengthIsSentInRequestAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));
        var textSearch = new KeenableTextSearch(options: new() { HttpClient = this._httpClient, SnippetMaxLength = 300 });

        // Act
        await textSearch.SearchAsync("What is the Semantic Kernel?", new() { Top = 4 });

        // Assert
        var requestBodyJson = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContents[0]!);
        Assert.Equal("{\"query\":\"What is the Semantic Kernel?\",\"max_results\":4,\"snippet_max_length\":300}", requestBodyJson);
    }

    [Fact]
    public async Task SkipIsAppliedToResultsAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));
        var textSearch = new KeenableTextSearch(options: new() { HttpClient = this._httpClient });

        // Act
        KernelSearchResults<TextSearchResult> result = await textSearch.GetTextSearchResultsAsync("What is the Semantic Kernel?", new() { Top = 3, Skip = 1 });
        var resultList = await result.Results.ToListAsync();

        // Assert - the API has no offset, so top + skip results are requested and the first skip are dropped
        var requestBodyJson = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContents[0]!);
        Assert.Contains("\"max_results\":4", requestBodyJson);
        Assert.Equal(3, resultList.Count);
        Assert.Equal("https://jacar.es/en/microsoft-semantic-kernel", resultList[0].Link);
    }

    [Theory]
    [InlineData(0, 0)]
    [InlineData(51, 0)]
    [InlineData(4, -1)]
    [InlineData(50, 1)]
    public async Task InvalidTopOrSkipThrowsAsync(int top, int skip)
    {
        // Arrange
        var textSearch = new KeenableTextSearch(options: new() { HttpClient = this._httpClient });

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentOutOfRangeException>(async () => await textSearch.SearchAsync("What is the Semantic Kernel?", new() { Top = top, Skip = skip }));
        Assert.Empty(this._messageHandlerStub.RequestUris);
    }

    [Theory]
    [InlineData(HttpStatusCode.TooManyRequests)]
    [InlineData(HttpStatusCode.BadRequest)]
    [InlineData(HttpStatusCode.Unauthorized)]
    [InlineData(HttpStatusCode.InternalServerError)]
    public async Task NonSuccessStatusCodeThrowsAsync(HttpStatusCode statusCode)
    {
        // Arrange
        this._messageHandlerStub.ResponsesToReturn.Add(new HttpResponseMessage(statusCode)
        {
            Content = new StringContent("{\"error\":\"rejected\"}", Encoding.UTF8, "application/json")
        });
        var textSearch = new KeenableTextSearch(options: new() { HttpClient = this._httpClient });

        // Act & Assert - a rejected request must surface as an exception, not as an empty result set
        var e = await Assert.ThrowsAsync<HttpOperationException>(async () => await textSearch.SearchAsync("What is the Semantic Kernel?", new() { Top = 4 }));
        Assert.Equal(statusCode, e.StatusCode);
    }

    [Fact]
    public async Task SearchWithCustomStringMapperReturnsSuccessfullyAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));

        // Create an ITextSearch instance using Keenable search
        var textSearch = new KeenableTextSearch(options: new() { HttpClient = this._httpClient, StringMapper = new TestTextSearchStringMapper() });

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
            var searchResult = JsonSerializer.Deserialize<KeenableSearchResult>(stringResult);
            Assert.NotNull(searchResult);
        }
    }

    [Fact]
    public async Task GetTextSearchResultsWithCustomResultMapperReturnsSuccessfullyAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));

        // Create an ITextSearch instance using Keenable search
        var textSearch = new KeenableTextSearch(options: new() { HttpClient = this._httpClient, ResultMapper = new TestTextSearchResultMapper() });

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

    [Theory]
    [InlineData("site", "learn.microsoft.com", "{\"query\":\"What is the Semantic Kernel?\",\"max_results\":4,\"site\":\"learn.microsoft.com\"}")]
    [InlineData("published_after", "2025-01-01", "{\"query\":\"What is the Semantic Kernel?\",\"max_results\":4,\"published_after\":\"2025-01-01\"}")]
    [InlineData("published_before", "2025-12-31", "{\"query\":\"What is the Semantic Kernel?\",\"max_results\":4,\"published_before\":\"2025-12-31\"}")]
    public async Task BuildsCorrectRequestForEqualityFilterAsync(string paramName, object paramValue, string request)
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(SiteFilterSKResponseJson));

        // Create an ITextSearch instance using Keenable search
        var textSearch = new KeenableTextSearch(options: new() { HttpClient = this._httpClient });

        // Act
        TextSearchOptions searchOptions = new() { Top = 4, Skip = 0, Filter = new TextSearchFilter().Equality(paramName, paramValue) };
        KernelSearchResults<object> result = await textSearch.GetSearchResultsAsync("What is the Semantic Kernel?", searchOptions);

        // Assert
        var requestContents = this._messageHandlerStub.RequestContents;
        Assert.Single(requestContents);
        Assert.NotNull(requestContents[0]);
        Assert.Equal(request, Encoding.UTF8.GetString(requestContents[0]!));

        var resultList = await result.Results.ToListAsync();
        Assert.Equal(3, resultList.Count);
        Assert.All(resultList, r => Assert.StartsWith("https://learn.microsoft.com/", ((KeenableSearchResult)r).Url, StringComparison.Ordinal));
    }

    [Fact]
    public async Task BuildsCorrectRequestForDateFilterValuesAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(SiteFilterSKResponseJson));
        var textSearch = new KeenableTextSearch(options: new() { HttpClient = this._httpClient });

        // Act - DateTime and DateTimeOffset values are formatted as YYYY-MM-DD
        TextSearchOptions searchOptions = new()
        {
            Top = 4,
            Filter = new TextSearchFilter()
                .Equality("published_after", new DateTime(2025, 1, 2, 13, 0, 0, DateTimeKind.Utc))
                .Equality("published_before", new DateTimeOffset(2025, 3, 4, 0, 0, 0, TimeSpan.Zero))
        };
        await textSearch.GetSearchResultsAsync("What is the Semantic Kernel?", searchOptions);

        // Assert
        var requestBodyJson = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContents[0]!);
        Assert.Equal("{\"query\":\"What is the Semantic Kernel?\",\"max_results\":4,\"published_after\":\"2025-01-02\",\"published_before\":\"2025-03-04\"}", requestBodyJson);
    }

    [Theory]
    [InlineData("fooBar", "baz")]
    public async Task DoesNotBuildRequestForInvalidQueryParameterAsync(string paramName, object paramValue)
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(SiteFilterSKResponseJson));
        TextSearchOptions searchOptions = new() { Top = 4, Skip = 0, Filter = new TextSearchFilter().Equality(paramName, paramValue) };

        // Create an ITextSearch instance using Keenable search
        var textSearch = new KeenableTextSearch(options: new() { HttpClient = this._httpClient });

        // Act && Assert
        var e = await Assert.ThrowsAsync<ArgumentException>(async () => await textSearch.GetSearchResultsAsync("What is the Semantic Kernel?", searchOptions));
        Assert.Contains("Unknown equality filter clause field name 'fooBar'", e.Message);
        Assert.Contains("site,published_after,published_before", e.Message);
    }

    [Fact]
    public async Task DoesNotBuildRequestForInvalidQueryAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(SiteFilterSKResponseJson));

        // Create an ITextSearch instance using Keenable search
        var textSearch = new KeenableTextSearch(options: new() { HttpClient = this._httpClient });

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

    #region Generic ITextSearch<KeenableWebPage> Interface Tests

    [Fact]
    public async Task LinqSearchAsyncReturnsResultsSuccessfullyAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(SiteFilterSKResponseJson));
        ITextSearch<KeenableWebPage> textSearch = new KeenableTextSearch(options: new() { HttpClient = this._httpClient });

        // Act
        var searchOptions = new TextSearchOptions<KeenableWebPage>
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
    public async Task LinqGetSearchResultsAsyncReturnsTypedResultsSuccessfullyAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(SiteFilterSKResponseJson));
        ITextSearch<KeenableWebPage> textSearch = new KeenableTextSearch(options: new() { HttpClient = this._httpClient });

        // Act
        var searchOptions = new TextSearchOptions<KeenableWebPage>
        {
            Top = 3,
            Skip = 0
        };
        KernelSearchResults<KeenableWebPage> result = await textSearch.GetSearchResultsAsync("What is the Semantic Kernel?", searchOptions);

        // Assert - Results are strongly typed as KeenableWebPage
        Assert.NotNull(result);
        Assert.NotNull(result.Results);
        var resultList = await result.Results.ToListAsync();
        Assert.Equal(3, resultList.Count);
        foreach (var page in resultList)
        {
            Assert.NotNull(page.Title);
            Assert.NotNull(page.Url);
            Assert.Equal("learn.microsoft.com", page.Url.Host);
            Assert.NotEmpty(page.Snippet!);
        }

        // Verify the request was made correctly
        var requestBodyJson = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContents[0]!);
        Assert.Contains("\"max_results\":3", requestBodyJson);
    }

    [Fact]
    public async Task LinqGetTextSearchResultsAsyncReturnsResultsSuccessfullyAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(SiteFilterSKResponseJson));
        ITextSearch<KeenableWebPage> textSearch = new KeenableTextSearch(options: new() { HttpClient = this._httpClient });

        // Act
        var searchOptions = new TextSearchOptions<KeenableWebPage>
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
        var requestBodyJson = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContents[0]!);
        Assert.Contains("\"max_results\":5", requestBodyJson);
    }

    [Fact]
    public async Task LinqEqualityFiltersMapToRequestFieldsAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(SiteFilterSKResponseJson));
        ITextSearch<KeenableWebPage> textSearch = new KeenableTextSearch(options: new() { HttpClient = this._httpClient });

        // Act
        var searchOptions = new TextSearchOptions<KeenableWebPage>
        {
            Top = 4,
            Skip = 0,
            Filter = page => page.Site == "learn.microsoft.com" && page.PublishedAfter == "2025-01-01" && page.PublishedBefore == "2025-12-31"
        };
        await textSearch.SearchAsync("What is the Semantic Kernel?", searchOptions);

        // Assert
        var requestBodyJson = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContents[0]!);
        Assert.Equal("{\"query\":\"What is the Semantic Kernel?\",\"max_results\":4,\"published_after\":\"2025-01-01\",\"published_before\":\"2025-12-31\",\"site\":\"learn.microsoft.com\"}", requestBodyJson);
    }

    [Fact]
    public async Task LinqUnsupportedPropertyThrowsNotSupportedExceptionAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(SiteFilterSKResponseJson));
        ITextSearch<KeenableWebPage> textSearch = new KeenableTextSearch(options: new() { HttpClient = this._httpClient });

        // Act & Assert - Description is a result field, not a filter
        var searchOptions = new TextSearchOptions<KeenableWebPage>
        {
            Top = 4,
            Filter = page => page.Description == "anything"
        };
        var exception = await Assert.ThrowsAsync<NotSupportedException>(async () => await textSearch.SearchAsync("test", searchOptions));
        Assert.Contains("Property 'Description' cannot be mapped", exception.Message);
        Assert.Empty(this._messageHandlerStub.RequestUris);
    }

    [Fact]
    public async Task CollectionContainsFilterThrowsNotSupportedExceptionAsync()
    {
        // Arrange - Tests both Enumerable.Contains (C# 13-) and MemoryExtensions.Contains (C# 14+)
        // The same code array.Contains() resolves differently based on C# language version:
        // - C# 13 and earlier: Enumerable.Contains (LINQ extension method)
        // - C# 14 and later: MemoryExtensions.Contains (span-based optimization due to "first-class spans")
        // Our implementation handles both identically since Keenable API has limited query operators
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(SiteFilterSKResponseJson));
        ITextSearch<KeenableWebPage> textSearch = new KeenableTextSearch(options: new() { HttpClient = this._httpClient });
        string[] sites = ["microsoft.com", "github.com"];

        // Act & Assert - Verify that collection Contains pattern throws clear exception
        var searchOptions = new TextSearchOptions<KeenableWebPage>
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
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(SiteFilterSKResponseJson));
        ITextSearch<KeenableWebPage> textSearch = new KeenableTextSearch(options: new() { HttpClient = this._httpClient });

        // Act - Title.Contains appends to the query, Site.Contains maps to the site filter
        var searchOptions = new TextSearchOptions<KeenableWebPage>
        {
            Top = 5,
            Skip = 0,
            Filter = page => page.Title.Contains("Kernel") && page.Site.Contains("learn.microsoft.com")
        };
        KernelSearchResults<string> result = await textSearch.SearchAsync("Semantic Kernel tutorial", searchOptions);

        // Assert - Verify String.Contains works correctly
        var requestBodyJson = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContents[0]!);
        Assert.Equal("{\"query\":\"Semantic Kernel tutorial Kernel\",\"max_results\":5,\"site\":\"learn.microsoft.com\"}", requestBodyJson);
    }

    #endregion

    #region private
    private const string WhatIsTheSKResponseJson = "./TestData/keenable_what_is_the_semantic_kernel.json";
    private const string SiteFilterSKResponseJson = "./TestData/keenable_site_filter_what_is_the_semantic_kernel.json";

    private readonly MultipleHttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;
    private readonly Kernel _kernel;

    /// <summary>
    /// Test mapper which converts a KeenableSearchResult to a string using JSON serialization.
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
    /// Test mapper which converts a KeenableSearchResult to an upper-cased TextSearchResult.
    /// </summary>
    private sealed class TestTextSearchResultMapper : ITextSearchResultMapper
    {
        /// <inheritdoc />
        public TextSearchResult MapFromResultToTextSearchResult(object result)
        {
            if (result is not KeenableSearchResult searchResult)
            {
                throw new ArgumentException("Result must be a KeenableSearchResult", nameof(result));
            }

            return new TextSearchResult(searchResult.Snippet?.ToUpperInvariant() ?? string.Empty)
            {
                Name = searchResult.Title?.ToUpperInvariant(),
                Link = searchResult.Url?.ToUpperInvariant(),
            };
        }
    }
    #endregion
}
