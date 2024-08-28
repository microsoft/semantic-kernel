// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.Web.Bing;
using Microsoft.SemanticKernel.Search;
using Xunit;

namespace SemanticKernel.Plugins.UnitTests.Web.Bing;

public sealed class BingTextSearchTests : IDisposable
{
    /// <summary>
    /// Initializes a new instance of the <see cref="BingTextSearchTests"/> class.
    /// </summary>
    public BingTextSearchTests()
    {
        this._messageHandlerStub = new MultipleHttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub, disposeHandler: false);
        this._kernel = new Kernel();
    }

    [Fact]
    public async Task SearchReturnsSuccessfullyAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));

        // Create an ITextSearch instance using Bing search
        var textSearch = new BingTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act
        KernelSearchResults<string> result = await textSearch.SearchAsync("What is the Semantic Kernel?", new() { Count = 10, Offset = 0 });

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
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));

        // Create an ITextSearch instance using Bing search
        var textSearch = new BingTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act
        KernelSearchResults<TextSearchResult> result = await textSearch.GetTextSearchResultsAsync("What is the Semantic Kernel?", new() { Count = 10, Offset = 0 });

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
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));

        // Create an ITextSearch instance using Bing search
        var textSearch = new BingTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act
        KernelSearchResults<object> result = await textSearch.GetSearchResultsAsync("What is the Semantic Kernel?", new() { Count = 10, Offset = 0 });

        // Assert
        Assert.NotNull(result);
        Assert.NotNull(result.Results);
        var resultList = await result.Results.ToListAsync();
        Assert.NotNull(resultList);
        Assert.Equal(10, resultList.Count);
        foreach (BingWebPage webPage in resultList)
        {
            Assert.NotNull(webPage.Name);
            Assert.NotNull(webPage.Snippet);
            Assert.NotNull(webPage.DateLastCrawled);
            Assert.NotNull(webPage.DisplayUrl);
            Assert.NotNull(webPage.Id);
        }
    }

    [Fact]
    public async Task SearchWithCustomMapperReturnsSuccessfullyAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));

        // Create an ITextSearch instance using Bing search
        var textSearch = new BingTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient, MapToString = webPage => JsonSerializer.Serialize(webPage) });

        // Act
        KernelSearchResults<string> result = await textSearch.SearchAsync("What is the Semantic Kernel?", new() { Count = 10, Offset = 0 });

        // Assert
        Assert.NotNull(result);
        Assert.NotNull(result.Results);
        var resultList = await result.Results.ToListAsync();
        Assert.NotNull(resultList);
        Assert.Equal(10, resultList.Count);
        foreach (var stringResult in resultList)
        {
            Assert.NotEmpty(stringResult);
            var webPage = JsonSerializer.Deserialize<BingWebPage>(stringResult);
            Assert.NotNull(webPage);
        }
    }

    [Theory]
    [InlineData("site", "devblogs.microsoft.com", "https://api.bing.microsoft.com/v7.0/search?q=What%20is%20the%20Semantic%20Kernel%3F+site%3Adevblogs.microsoft.com&count=4&offset=0")]
    [InlineData("answerCount", 5, "https://api.bing.microsoft.com/v7.0/search?q=What%20is%20the%20Semantic%20Kernel%3F&count=4&offset=0&answerCount=5")]
    [InlineData("cc", "AR", "https://api.bing.microsoft.com/v7.0/search?q=What%20is%20the%20Semantic%20Kernel%3F&count=4&offset=0&cc=AR")]
    [InlineData("freshness", "2019-02-01..2019-05-30", "https://api.bing.microsoft.com/v7.0/search?q=What%20is%20the%20Semantic%20Kernel%3F&count=4&offset=0&freshness=2019-02-01..2019-05-30")]
    [InlineData("mkt", "es-AR", "https://api.bing.microsoft.com/v7.0/search?q=What%20is%20the%20Semantic%20Kernel%3F&count=4&offset=0&mkt=es-AR")]
    [InlineData("promote", "Computation,SpellSuggestions", "https://api.bing.microsoft.com/v7.0/search?q=What%20is%20the%20Semantic%20Kernel%3F&count=4&offset=0&promote=Computation%2CSpellSuggestions")]
    [InlineData("responseFilter", "Computation,SpellSuggestions", "https://api.bing.microsoft.com/v7.0/search?q=What%20is%20the%20Semantic%20Kernel%3F&count=4&offset=0&responseFilter=Computation%2CSpellSuggestions")]
    [InlineData("safeSearch", "Strict", "https://api.bing.microsoft.com/v7.0/search?q=What%20is%20the%20Semantic%20Kernel%3F&count=4&offset=0&safeSearch=Strict")]
    [InlineData("setLang", "ar", "https://api.bing.microsoft.com/v7.0/search?q=What%20is%20the%20Semantic%20Kernel%3F&count=4&offset=0&setLang=ar")]
    [InlineData("textDecorations", true, "https://api.bing.microsoft.com/v7.0/search?q=What%20is%20the%20Semantic%20Kernel%3F&count=4&offset=0&textDecorations=True")]
    [InlineData("textFormat", "HTML", "https://api.bing.microsoft.com/v7.0/search?q=What%20is%20the%20Semantic%20Kernel%3F&count=4&offset=0&textFormat=HTML")]
    public async Task BuildsCorrectUriForEqualityFilterAsync(string paramName, object paramValue, string requestLink)
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(SiteFilterDevBlogsResponseJson));

        // Create an ITextSearch instance using Bing search
        var textSearch = new BingTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act
        TextSearchOptions searchOptions = new() { Count = 4, Offset = 0, BasicFilter = new BasicFilterOptions().Equality(paramName, paramValue) };
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
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(SiteFilterDevBlogsResponseJson));
        TextSearchOptions searchOptions = new() { Count = 4, Offset = 0, BasicFilter = new BasicFilterOptions().Equality("fooBar", "Baz") };

        // Create an ITextSearch instance using Bing search
        var textSearch = new BingTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act && Assert
        var e = await Assert.ThrowsAsync<ArgumentException>(async () => await textSearch.GetSearchResultsAsync("What is the Semantic Kernel?", searchOptions));
        Assert.Equal("Unknown equality filter clause field name, must be one of answerCount,cc,freshness,mkt,promote,responseFilter,safeSearch,setLang,textDecorations,textFormat (Parameter 'searchOptions')", e.Message);
    }

    /// <inheritdoc/>
    public void Dispose()
    {
        this._messageHandlerStub.Dispose();
        this._httpClient.Dispose();

        GC.SuppressFinalize(this);
    }

    #region private
    private const string WhatIsTheSKResponseJson = "./TestData/bing_what_is_the_semantic_kernel.json";
    private const string SiteFilterDevBlogsResponseJson = "./TestData/bing_site_filter_devblogs_microsoft.com.json";

    private readonly MultipleHttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;
    private readonly Kernel _kernel;
    #endregion
}
