// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using Google.Apis.CustomSearchAPI.v1.Data;
using Google.Apis.Http;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Plugins.Web.Google;
using Xunit;

namespace SemanticKernel.Plugins.UnitTests.Web.Google;

public sealed class GoogleTextSearchTests : IDisposable
{
    /// <summary>
    /// Initializes a new instance of the <see cref="GoogleTextSearchTests"/> class.
    /// </summary>
    public GoogleTextSearchTests()
    {
        this._messageHandlerStub = new MultipleHttpMessageHandlerStub();
        this._clientFactory = new CustomHttpClientFactory(this._messageHandlerStub);
        this._kernel = new Kernel();
    }

    [Fact]
    public void AddGoogleTextSearchSucceeds()
    {
        // Arrange
        var builder = Kernel.CreateBuilder();

        // Act
        builder.AddGoogleTextSearch(searchEngineId: "searchEngineId", apiKey: "ApiKey");
        var kernel = builder.Build();

        // Assert
        Assert.IsType<GoogleTextSearch>(kernel.Services.GetRequiredService<ITextSearch>());
    }

    [Fact]
    public async Task SearchReturnsSuccessfullyAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));

        // Create an ITextSearch instance using Google search
        using var textSearch = new GoogleTextSearch(
            initializer: new() { ApiKey = "ApiKey", HttpClientFactory = this._clientFactory },
            searchEngineId: "SearchEngineId");

        // Act
        var results = textSearch.SearchAsync("What is the Semantic Kernel?", 4, new() { Skip = 0 });

        // Assert
        Assert.NotNull(results);
        var resultList = await results.ToListAsync();
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

        // Create an ITextSearch instance using Google search
        using var textSearch = new GoogleTextSearch(
            initializer: new() { ApiKey = "ApiKey", HttpClientFactory = this._clientFactory },
            searchEngineId: "SearchEngineId");

        // Act
        var results = textSearch.GetTextSearchResultsAsync("What is the Semantic Kernel?", 10, new() { Skip = 0 });

        // Assert
        Assert.NotNull(results);
        var resultList = await results.ToListAsync();
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

        // Create an ITextSearch instance using Google search
        using var textSearch = new GoogleTextSearch(
            initializer: new() { ApiKey = "ApiKey", HttpClientFactory = this._clientFactory },
            searchEngineId: "SearchEngineId");

        // Act
        var results = textSearch.GetSearchResultsAsync("What is the Semantic Kernel?", 10, new() { Skip = 0 });

        // Assert
        Assert.NotNull(results);
        var resultList = await results.ToListAsync();
        Assert.NotNull(resultList);
        Assert.Equal(4, resultList.Count);
        foreach (Result result in resultList.Cast<Result>())
        {
            Assert.NotNull(result.Title);
            Assert.NotNull(result.Snippet);
            Assert.NotNull(result.Link);
            Assert.NotNull(result.DisplayLink);
            Assert.NotNull(result.Kind);
        }
    }

    [Fact]
    public async Task SearchWithCustomStringMapperReturnsSuccessfullyAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));

        // Create an ITextSearch instance using Google search
        using var textSearch = new GoogleTextSearch(
            initializer: new() { ApiKey = "ApiKey", HttpClientFactory = this._clientFactory },
            searchEngineId: "SearchEngineId",
            options: new() { StringMapper = new TestTextSearchStringMapper() });

        // Act
        var results = textSearch.SearchAsync("What is the Semantic Kernel?", 4, new() { Skip = 0 });

        // Assert
        Assert.NotNull(results);
        var resultList = await results.ToListAsync();
        Assert.NotNull(resultList);
        Assert.Equal(4, resultList.Count);
        foreach (var stringResult in resultList)
        {
            Assert.NotEmpty(stringResult);
            var googleResult = JsonSerializer.Deserialize<global::Google.Apis.CustomSearchAPI.v1.Data.Result>(stringResult);
            Assert.NotNull(googleResult);
        }
    }

    [Fact]
    public async Task GetTextSearchResultsWithCustomResultMapperReturnsSuccessfullyAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));

        // Create an ITextSearch instance using Google search
        using var textSearch = new GoogleTextSearch(
            initializer: new() { ApiKey = "ApiKey", HttpClientFactory = this._clientFactory },
            searchEngineId: "SearchEngineId",
            options: new() { ResultMapper = new TestTextSearchResultMapper() });

        // Act
        var results = textSearch.GetTextSearchResultsAsync("What is the Semantic Kernel?", 4, new() { Skip = 0 });

        // Assert
        Assert.NotNull(results);
        var resultList = await results.ToListAsync();
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
    [InlineData("cr", "countryAF", "https://customsearch.googleapis.com/customsearch/v1?key=ApiKey&cr=countryAF&cx=SearchEngineId&num=4&q=What%20is%20the%20Semantic%20Kernel%3F&start=0")]
    [InlineData("dateRestrict", "d[5]", "https://customsearch.googleapis.com/customsearch/v1?key=ApiKey&cx=SearchEngineId&dateRestrict=d%5B5%5D&num=4&q=What%20is%20the%20Semantic%20Kernel%3F&start=0")]
    [InlineData("exactTerms", "Semantic Kernel", "https://customsearch.googleapis.com/customsearch/v1?key=ApiKey&cx=SearchEngineId&exactTerms=Semantic%20Kernel&num=4&q=What%20is%20the%20Semantic%20Kernel%3F&start=0")]
    [InlineData("excludeTerms", "FooBar", "https://customsearch.googleapis.com/customsearch/v1?key=ApiKey&cx=SearchEngineId&excludeTerms=FooBar&num=4&q=What%20is%20the%20Semantic%20Kernel%3F&start=0")]
    [InlineData("filter", "0", "https://customsearch.googleapis.com/customsearch/v1?key=ApiKey&cx=SearchEngineId&filter=0&num=4&q=What%20is%20the%20Semantic%20Kernel%3F&start=0")]
    [InlineData("gl", "ie", "https://customsearch.googleapis.com/customsearch/v1?key=ApiKey&cx=SearchEngineId&gl=ie&num=4&q=What%20is%20the%20Semantic%20Kernel%3F&start=0")]
    [InlineData("hl", "en", "https://customsearch.googleapis.com/customsearch/v1?key=ApiKey&cx=SearchEngineId&hl=en&num=4&q=What%20is%20the%20Semantic%20Kernel%3F&start=0")]
    [InlineData("linkSite", "http://example.com", "https://customsearch.googleapis.com/customsearch/v1?key=ApiKey&cx=SearchEngineId&linkSite=http%3A%2F%2Fexample.com&num=4&q=What%20is%20the%20Semantic%20Kernel%3F&start=0")]
    [InlineData("lr", "lang_ar", "https://customsearch.googleapis.com/customsearch/v1?key=ApiKey&cx=SearchEngineId&lr=lang_ar&num=4&q=What%20is%20the%20Semantic%20Kernel%3F&start=0")]
    [InlineData("orTerms", "Microsoft", "https://customsearch.googleapis.com/customsearch/v1?key=ApiKey&cx=SearchEngineId&num=4&orTerms=Microsoft&q=What%20is%20the%20Semantic%20Kernel%3F&start=0")]
    [InlineData("rights", "cc_publicdomain", "https://customsearch.googleapis.com/customsearch/v1?key=ApiKey&cx=SearchEngineId&num=4&q=What%20is%20the%20Semantic%20Kernel%3F&rights=cc_publicdomain&start=0")]
    [InlineData("siteSearch", "devblogs.microsoft.com", "https://customsearch.googleapis.com/customsearch/v1?key=ApiKey&cx=SearchEngineId&num=4&q=What%20is%20the%20Semantic%20Kernel%3F&siteSearch=devblogs.microsoft.com&siteSearchFilter=i&start=0")]
    public async Task BuildsCorrectUriForEqualityFilterAsync(string paramName, object paramValue, string requestLink)
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(SiteFilterDevBlogsResponseJson));

        // Create an ITextSearch instance using Google search
        using var textSearch = new GoogleTextSearch(
            initializer: new() { ApiKey = "ApiKey", HttpClientFactory = this._clientFactory },
            searchEngineId: "SearchEngineId");

        // Act
        TextSearchOptions searchOptions = new() { Skip = 0, Filter = new TextSearchFilter().Equality(paramName, paramValue) };
        var results = await textSearch.GetSearchResultsAsync("What is the Semantic Kernel?", 4, searchOptions).ToListAsync();

        // Assert
        var requestUris = this._messageHandlerStub.RequestUris;
        Assert.Single(requestUris);
        Assert.NotNull(requestUris[0]);
        var absoluteUri = requestUris[0]!.AbsoluteUri;
        Assert.Equal(requestLink, requestUris[0]!.AbsoluteUri);
    }

    [Fact]
    public async Task DoesNotBuildsUriForInvalidQueryParameterAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(SiteFilterDevBlogsResponseJson));
        TextSearchOptions searchOptions = new() { Skip = 0, Filter = new TextSearchFilter().Equality("fooBar", "Baz") };

        using var textSearch = new GoogleTextSearch(
            initializer: new() { ApiKey = "ApiKey", HttpClientFactory = this._clientFactory },
            searchEngineId: "SearchEngineId");

        // Act && Assert
        var e = await Assert.ThrowsAsync<ArgumentException>(async () => await textSearch.GetSearchResultsAsync("What is the Semantic Kernel?", 4, searchOptions).ToListAsync());
        Assert.Equal("Unknown equality filter clause field name 'fooBar', must be one of cr,dateRestrict,exactTerms,excludeTerms,filter,gl,hl,linkSite,lr,orTerms,rights,siteSearch (Parameter 'searchOptions')", e.Message);
    }

    /// <inheritdoc/>
    public void Dispose()
    {
        this._messageHandlerStub.Dispose();
        this._clientFactory.Dispose();

        GC.SuppressFinalize(this);
    }

    #region private
    private const string WhatIsTheSKResponseJson = "./TestData/google_what_is_the_semantic_kernel.json";
    private const string SiteFilterDevBlogsResponseJson = "./TestData/google_site_filter_devblogs_microsoft.com.json";

    private readonly MultipleHttpMessageHandlerStub _messageHandlerStub;
    private readonly CustomHttpClientFactory _clientFactory;
    private readonly Kernel _kernel;

    /// <summary>
    /// Implementation of <see cref="IHttpClientFactory"/> which uses the <see cref="MultipleHttpMessageHandlerStub"/>.
    /// </summary>
    private sealed class CustomHttpClientFactory(MultipleHttpMessageHandlerStub handlerStub) : IHttpClientFactory, IDisposable
    {
        private readonly ConfigurableMessageHandler _messageHandler = new(handlerStub);

        public ConfigurableHttpClient CreateHttpClient(CreateHttpClientArgs args)
        {
            var configurableHttpClient = new ConfigurableHttpClient(this._messageHandler);
            return configurableHttpClient;
        }

        public void Dispose()
        {
            this._messageHandler.Dispose();

            GC.SuppressFinalize(this);
        }
    }

    /// <summary>
    /// Test mapper which converts a global::Google.Apis.CustomSearchAPI.v1.Data.Result search result to a string using JSON serialization.
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
    /// Test mapper which converts a global::Google.Apis.CustomSearchAPI.v1.Data.Result search result to a string using JSON serialization.
    /// </summary>
    private sealed class TestTextSearchResultMapper : ITextSearchResultMapper
    {
        /// <inheritdoc />
        public TextSearchResult MapFromResultToTextSearchResult(object result)
        {
            if (result is not global::Google.Apis.CustomSearchAPI.v1.Data.Result googleResult)
            {
                throw new ArgumentException("Result must be a Google Result", nameof(result));
            }

            return new TextSearchResult(googleResult.Snippet?.ToUpperInvariant() ?? string.Empty)
            {
                Name = googleResult.Title?.ToUpperInvariant(),
                Link = googleResult.Link?.ToUpperInvariant(),
            };
        }
    }
    #endregion
}
