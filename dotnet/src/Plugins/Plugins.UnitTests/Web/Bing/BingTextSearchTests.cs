// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable CS0618 // ITextSearch is obsolete

using System;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Plugins.Web.Bing;
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
    public void AddBingTextSearchSucceeds()
    {
        // Arrange
        var builder = Kernel.CreateBuilder();

        // Act
        builder.AddBingTextSearch(apiKey: "ApiKey");
        var kernel = builder.Build();

        // Assert
        Assert.IsType<BingTextSearch>(kernel.Services.GetRequiredService<ITextSearch>());
    }

    [Fact]
    public async Task SearchReturnsSuccessfullyAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));

        // Create an ITextSearch instance using Bing search
        var textSearch = new BingTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

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
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));

        // Create an ITextSearch instance using Bing search
        var textSearch = new BingTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

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
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));

        // Create an ITextSearch instance using Bing search
        var textSearch = new BingTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act
        KernelSearchResults<object> result = await textSearch.GetSearchResultsAsync("What is the Semantic Kernel?", new() { Top = 10, Skip = 0 });

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
    public async Task SearchWithCustomStringMapperReturnsSuccessfullyAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));

        // Create an ITextSearch instance using Bing search
        var textSearch = new BingTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient, StringMapper = new TestTextSearchStringMapper() });

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
            var webPage = JsonSerializer.Deserialize<BingWebPage>(stringResult);
            Assert.NotNull(webPage);
        }
    }

    [Fact]
    public async Task GetTextSearchResultsWithCustomResultMapperReturnsSuccessfullyAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));

        // Create an ITextSearch instance using Bing search
        var textSearch = new BingTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient, ResultMapper = new TestTextSearchResultMapper() });

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

    [Theory]
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
    [InlineData("contains", "wma", "https://api.bing.microsoft.com/v7.0/search?q=What%20is%20the%20Semantic%20Kernel%3F+contains%3Awma&count=4&offset=0")]
    [InlineData("ext", "docx", "https://api.bing.microsoft.com/v7.0/search?q=What%20is%20the%20Semantic%20Kernel%3F+ext%3Adocx&count=4&offset=0")]
    [InlineData("filetype", "pdf", "https://api.bing.microsoft.com/v7.0/search?q=What%20is%20the%20Semantic%20Kernel%3F+filetype%3Apdf&count=4&offset=0")]
    [InlineData("inanchor", "msn", "https://api.bing.microsoft.com/v7.0/search?q=What%20is%20the%20Semantic%20Kernel%3F+inanchor%3Amsn&count=4&offset=0")]
    [InlineData("inbody", "msn", "https://api.bing.microsoft.com/v7.0/search?q=What%20is%20the%20Semantic%20Kernel%3F+inbody%3Amsn&count=4&offset=0")]
    [InlineData("intitle", "msn", "https://api.bing.microsoft.com/v7.0/search?q=What%20is%20the%20Semantic%20Kernel%3F+intitle%3Amsn&count=4&offset=0")]
    [InlineData("ip", "127.0.0.1", "https://api.bing.microsoft.com/v7.0/search?q=What%20is%20the%20Semantic%20Kernel%3F+ip%3A127.0.0.1&count=4&offset=0")]
    [InlineData("language", "en", "https://api.bing.microsoft.com/v7.0/search?q=What%20is%20the%20Semantic%20Kernel%3F+language%3Aen&count=4&offset=0")]
    [InlineData("loc", "IE", "https://api.bing.microsoft.com/v7.0/search?q=What%20is%20the%20Semantic%20Kernel%3F+loc%3AIE&count=4&offset=0")]
    [InlineData("location", "IE", "https://api.bing.microsoft.com/v7.0/search?q=What%20is%20the%20Semantic%20Kernel%3F+location%3AIE&count=4&offset=0")]
    [InlineData("prefer", "organization", "https://api.bing.microsoft.com/v7.0/search?q=What%20is%20the%20Semantic%20Kernel%3F+prefer%3Aorganization&count=4&offset=0")]
    [InlineData("feed", "football", "https://api.bing.microsoft.com/v7.0/search?q=What%20is%20the%20Semantic%20Kernel%3F+feed%3Afootball&count=4&offset=0")]
    [InlineData("hasfeed", "football", "https://api.bing.microsoft.com/v7.0/search?q=What%20is%20the%20Semantic%20Kernel%3F+hasfeed%3Afootball&count=4&offset=0")]
    [InlineData("url", "microsoft.com", "https://api.bing.microsoft.com/v7.0/search?q=What%20is%20the%20Semantic%20Kernel%3F+url%3Amicrosoft.com&count=4&offset=0")]
    [InlineData("site", "devblogs.microsoft.com", "https://api.bing.microsoft.com/v7.0/search?q=What%20is%20the%20Semantic%20Kernel%3F+site%3Adevblogs.microsoft.com&count=4&offset=0")]
    public async Task BuildsCorrectUriForEqualityFilterAsync(string paramName, object paramValue, string requestLink)
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(SiteFilterDevBlogsResponseJson));

        // Create an ITextSearch instance using Bing search
        var textSearch = new BingTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act
        TextSearchOptions searchOptions = new() { Top = 4, Skip = 0, Filter = new TextSearchFilter().Equality(paramName, paramValue) };
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
        TextSearchOptions searchOptions = new() { Top = 4, Skip = 0, Filter = new TextSearchFilter().Equality("fooBar", "Baz") };

        // Create an ITextSearch instance using Bing search
        var textSearch = new BingTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act && Assert
        var e = await Assert.ThrowsAsync<ArgumentException>(async () => await textSearch.GetSearchResultsAsync("What is the Semantic Kernel?", searchOptions));
        Assert.Equal("Unknown equality filter clause field name 'fooBar', must be one of answerCount,cc,freshness,mkt,promote,responseFilter,safeSearch,setLang,textDecorations,textFormat,contains,ext,filetype,inanchor,inbody,intitle,ip,language,loc,location,prefer,site,feed,hasfeed,url (Parameter 'searchOptions')", e.Message);
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

    /// <summary>
    /// Test mapper which converts a BingWebPage search result to a string using JSON serialization.
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
    /// Test mapper which converts a BingWebPage search result to a string using JSON serialization.
    /// </summary>
    private sealed class TestTextSearchResultMapper : ITextSearchResultMapper
    {
        /// <inheritdoc />
        public TextSearchResult MapFromResultToTextSearchResult(object result)
        {
            if (result is not BingWebPage webPage)
            {
                throw new ArgumentException("Result must be a BingWebPage", nameof(result));
            }

            return new TextSearchResult(webPage.Snippet?.ToUpperInvariant() ?? string.Empty)
            {
                Name = webPage.Name?.ToUpperInvariant(),
                Link = webPage.DisplayUrl?.ToUpperInvariant(),
            };
        }
    }
    #endregion
}
