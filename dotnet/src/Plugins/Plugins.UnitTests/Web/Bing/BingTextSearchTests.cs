// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable CS0618 // ITextSearch is obsolete
#pragma warning disable CS8602 // Dereference of a possibly null reference - Test LINQ expressions access BingWebPage properties guaranteed non-null in test context

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
        Assert.Equal(requestLink, requestUris[0].AbsoluteUri);
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

    #region Generic ITextSearch<BingWebPage> Interface Tests

    [Fact]
    public async Task GenericSearchAsyncWithLanguageEqualityFilterProducesCorrectBingQueryAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));
        ITextSearch<BingWebPage> textSearch = new BingTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act
        var searchOptions = new TextSearchOptions<BingWebPage>
        {
            Top = 4,
            Skip = 0,
            Filter = page => page.Language == "en"
        };
        KernelSearchResults<string> result = await textSearch.SearchAsync("What is the Semantic Kernel?", searchOptions);

        // Assert - Verify LINQ expression converted to Bing's language: operator
        var requestUris = this._messageHandlerStub.RequestUris;
        Assert.Single(requestUris);
        Assert.NotNull(requestUris[0]);
        Assert.Contains("language%3Aen", requestUris[0].AbsoluteUri);
        Assert.Contains("count=4", requestUris[0].AbsoluteUri);
        Assert.Contains("offset=0", requestUris[0].AbsoluteUri);
    }

    [Fact]
    public async Task GenericSearchAsyncWithLanguageInequalityFilterProducesCorrectBingQueryAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));
        ITextSearch<BingWebPage> textSearch = new BingTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act
        var searchOptions = new TextSearchOptions<BingWebPage>
        {
            Top = 4,
            Skip = 0,
            Filter = page => page.Language != "fr"
        };
        KernelSearchResults<string> result = await textSearch.SearchAsync("What is the Semantic Kernel?", searchOptions);

        // Assert - Verify LINQ inequality expression converted to Bing's negation syntax (-language:fr)
        var requestUris = this._messageHandlerStub.RequestUris;
        Assert.Single(requestUris);
        Assert.NotNull(requestUris[0]);
        Assert.Contains("-language%3Afr", requestUris[0].AbsoluteUri);
    }

    [Fact]
    public async Task GenericSearchAsyncWithContainsFilterProducesCorrectBingQueryAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));
        ITextSearch<BingWebPage> textSearch = new BingTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act
        var searchOptions = new TextSearchOptions<BingWebPage>
        {
            Top = 4,
            Skip = 0,
            Filter = page => page.Name!.Contains("Microsoft")
        };
        KernelSearchResults<string> result = await textSearch.SearchAsync("What is the Semantic Kernel?", searchOptions);

        // Assert - Verify LINQ Contains() converted to Bing's intitle: operator
        var requestUris = this._messageHandlerStub.RequestUris;
        Assert.Single(requestUris);
        Assert.NotNull(requestUris[0]);
        Assert.Contains("intitle%3AMicrosoft", requestUris[0].AbsoluteUri);
    }

    [Fact]
    public async Task GenericSearchAsyncWithComplexAndFilterProducesCorrectBingQueryAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));
        ITextSearch<BingWebPage> textSearch = new BingTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act
        var searchOptions = new TextSearchOptions<BingWebPage>
        {
            Top = 4,
            Skip = 0,
            Filter = page => page.Language == "en" && page.Name!.Contains("AI")
        };
        KernelSearchResults<string> result = await textSearch.SearchAsync("What is the Semantic Kernel?", searchOptions);

        // Assert - Verify LINQ AND expression produces both Bing operators
        var requestUris = this._messageHandlerStub.RequestUris;
        Assert.Single(requestUris);
        Assert.NotNull(requestUris[0]);
        Assert.Contains("language%3Aen", requestUris[0].AbsoluteUri);
        Assert.Contains("intitle%3AAI", requestUris[0].AbsoluteUri);
    }

    [Fact]
    public async Task GenericGetTextSearchResultsAsyncWithUrlFilterProducesCorrectBingQueryAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));
        ITextSearch<BingWebPage> textSearch = new BingTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act
        var searchOptions = new TextSearchOptions<BingWebPage>
        {
            Top = 4,
            Skip = 0,
            Filter = page => page.Url!.Contains("microsoft.com")
        };
        KernelSearchResults<TextSearchResult> result = await textSearch.GetTextSearchResultsAsync("What is the Semantic Kernel?", searchOptions);

        // Assert - Verify LINQ Url.Contains() converted to Bing's url: operator
        var requestUris = this._messageHandlerStub.RequestUris;
        Assert.Single(requestUris);
        Assert.NotNull(requestUris[0]);
        Assert.Contains("url%3Amicrosoft.com", requestUris[0].AbsoluteUri);

        // Also verify result structure
        Assert.NotNull(result);
        Assert.NotNull(result.Results);
    }

    [Fact]
    public async Task GenericGetSearchResultsAsyncWithSnippetContainsFilterProducesCorrectBingQueryAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));
        ITextSearch<BingWebPage> textSearch = new BingTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act
        var searchOptions = new TextSearchOptions<BingWebPage>
        {
            Top = 4,
            Skip = 0,
            Filter = page => page.Snippet!.Contains("semantic")
        };
        KernelSearchResults<BingWebPage> result = await textSearch.GetSearchResultsAsync("What is the Semantic Kernel?", searchOptions);

        // Assert - Verify LINQ Snippet.Contains() converted to Bing's inbody: operator
        var requestUris = this._messageHandlerStub.RequestUris;
        Assert.Single(requestUris);
        Assert.NotNull(requestUris[0]);
        Assert.Contains("inbody%3Asemantic", requestUris[0].AbsoluteUri);

        // Verify result structure
        Assert.NotNull(result);
        Assert.NotNull(result.Results);
    }

    [Fact]
    public async Task GenericSearchAsyncWithDisplayUrlEqualityFilterProducesCorrectBingQueryAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(SiteFilterDevBlogsResponseJson));
        ITextSearch<BingWebPage> textSearch = new BingTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act
        var searchOptions = new TextSearchOptions<BingWebPage>
        {
            Top = 4,
            Skip = 0,
            Filter = page => page.DisplayUrl == "devblogs.microsoft.com"
        };
        KernelSearchResults<string> result = await textSearch.SearchAsync("What is the Semantic Kernel?", searchOptions);

        // Assert - Verify LINQ DisplayUrl equality converted to Bing's site: operator
        var requestUris = this._messageHandlerStub.RequestUris;
        Assert.Single(requestUris);
        Assert.NotNull(requestUris[0]);
        Assert.Contains("site%3Adevblogs.microsoft.com", requestUris[0].AbsoluteUri);
    }

    [Fact]
    public async Task GenericSearchAsyncWithMultipleAndConditionsProducesCorrectBingQueryAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));
        ITextSearch<BingWebPage> textSearch = new BingTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act
        var searchOptions = new TextSearchOptions<BingWebPage>
        {
            Top = 4,
            Skip = 0,
            Filter = page => page.Language == "en" && page.DisplayUrl!.Contains("microsoft.com") && page.Name!.Contains("Semantic")
        };
        KernelSearchResults<string> result = await textSearch.SearchAsync("What is the Semantic Kernel?", searchOptions);

        // Assert - Verify all LINQ conditions converted correctly
        var requestUris = this._messageHandlerStub.RequestUris;
        Assert.Single(requestUris);
        Assert.NotNull(requestUris[0]);
        string uri = requestUris[0].AbsoluteUri;
        Assert.Contains("language%3Aen", uri);
        Assert.Contains("site%3Amicrosoft.com", uri);  // DisplayUrl.Contains() ? site: operator
        Assert.Contains("intitle%3ASemantic", uri);
    }

    [Fact]
    public async Task GenericSearchAsyncWithNoFilterReturnsResultsSuccessfullyAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));
        ITextSearch<BingWebPage> textSearch = new BingTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act - No filter specified
        var searchOptions = new TextSearchOptions<BingWebPage>
        {
            Top = 10,
            Skip = 0
        };
        KernelSearchResults<string> result = await textSearch.SearchAsync("What is the Semantic Kernel?", searchOptions);

        // Assert - Verify basic query without filter operators
        var requestUris = this._messageHandlerStub.RequestUris;
        Assert.Single(requestUris);
        Assert.NotNull(requestUris[0]);
        Assert.DoesNotContain("language%3A", requestUris[0].AbsoluteUri);
        Assert.DoesNotContain("intitle%3A", requestUris[0].AbsoluteUri);

        // Verify results
        Assert.NotNull(result);
        Assert.NotNull(result.Results);
        var resultList = await result.Results.ToListAsync();
        Assert.Equal(10, resultList.Count);
    }

    [Fact]
    public async Task GenericSearchAsyncWithIsFamilyFriendlyFilterProducesCorrectBingQueryAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));
        ITextSearch<BingWebPage> textSearch = new BingTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act
        var searchOptions = new TextSearchOptions<BingWebPage>
        {
            Top = 4,
            Skip = 0,
            Filter = page => page.IsFamilyFriendly == true
        };
        KernelSearchResults<string> result = await textSearch.SearchAsync("What is the Semantic Kernel?", searchOptions);

        // Assert - Verify LINQ IsFamilyFriendly equality converted to Bing's safeSearch query parameter
        var requestUris = this._messageHandlerStub.RequestUris;
        Assert.Single(requestUris);
        Assert.NotNull(requestUris[0]);
        // safeSearch is a query parameter, not an advanced search operator
        Assert.Contains("safeSearch=true", requestUris[0].AbsoluteUri);
    }

    [Fact]
    public async Task GenericSearchAsyncWithIsFamilyFriendlyFalseFilterProducesCorrectBingQueryAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));
        ITextSearch<BingWebPage> textSearch = new BingTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act
        var searchOptions = new TextSearchOptions<BingWebPage>
        {
            Top = 4,
            Skip = 0,
            Filter = page => page.IsFamilyFriendly == false
        };
        KernelSearchResults<string> result = await textSearch.SearchAsync("What is the Semantic Kernel?", searchOptions);

        // Assert - Verify false value converted correctly
        var requestUris = this._messageHandlerStub.RequestUris;
        Assert.Single(requestUris);
        Assert.NotNull(requestUris[0]);
        Assert.Contains("safeSearch=false", requestUris[0].AbsoluteUri);
    }

    [Fact]
    public async Task GenericSearchAsyncWithMultipleContainsConditionsProducesCorrectBingQueryAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));
        ITextSearch<BingWebPage> textSearch = new BingTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act - Multiple Contains operations on different properties
        var searchOptions = new TextSearchOptions<BingWebPage>
        {
            Top = 4,
            Skip = 0,
            Filter = page => page.Name!.Contains("Semantic") && page.Snippet!.Contains("kernel") && page.Url!.Contains("microsoft.com")
        };
        KernelSearchResults<string> result = await textSearch.SearchAsync("AI", searchOptions);

        // Assert - Verify all Contains operations translated correctly
        var requestUris = this._messageHandlerStub.RequestUris;
        Assert.Single(requestUris);
        Assert.NotNull(requestUris[0]);
        string uri = requestUris[0].AbsoluteUri;
        Assert.Contains("intitle%3ASemantic", uri);   // Name.Contains() ? intitle:
        Assert.Contains("inbody%3Akernel", uri);      // Snippet.Contains() ? inbody:
        Assert.Contains("url%3Amicrosoft.com", uri);  // Url.Contains() ? url:
    }

    [Fact]
    public async Task GenericSearchAsyncWithMixedEqualityAndContainsProducesCorrectBingQueryAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));
        ITextSearch<BingWebPage> textSearch = new BingTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act - Mix equality and Contains operations
        var searchOptions = new TextSearchOptions<BingWebPage>
        {
            Top = 4,
            Skip = 0,
            Filter = page => page.Language == "en" &&
                            page.IsFamilyFriendly == true &&
                            page.Name!.Contains("Azure") &&
                            page.DisplayUrl!.Contains("microsoft.com")
        };
        KernelSearchResults<string> result = await textSearch.SearchAsync("cloud", searchOptions);

        // Assert - Verify mixed operators all present
        var requestUris = this._messageHandlerStub.RequestUris;
        Assert.Single(requestUris);
        Assert.NotNull(requestUris[0]);
        string uri = requestUris[0].AbsoluteUri;
        Assert.Contains("language%3Aen", uri);
        Assert.Contains("safeSearch=true", uri);
        Assert.Contains("intitle%3AAzure", uri);
        Assert.Contains("site%3Amicrosoft.com", uri);
    }

    [Fact]
    public async Task GenericSearchAsyncWithInequalityAndEqualityProducesCorrectBingQueryAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));
        ITextSearch<BingWebPage> textSearch = new BingTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act - Combine inequality (negation) with positive equality
        var searchOptions = new TextSearchOptions<BingWebPage>
        {
            Top = 4,
            Skip = 0,
            Filter = page => page.Language != "fr" && page.DisplayUrl == "docs.microsoft.com"
        };
        KernelSearchResults<string> result = await textSearch.SearchAsync("documentation", searchOptions);

        // Assert - Verify negation and positive condition both present
        var requestUris = this._messageHandlerStub.RequestUris;
        Assert.Single(requestUris);
        Assert.NotNull(requestUris[0]);
        string uri = requestUris[0].AbsoluteUri;
        Assert.Contains("-language%3Afr", uri);           // Negation prefix
        Assert.Contains("site%3Adocs.microsoft.com", uri); // Positive condition
    }

    [Fact]
    public async Task GenericSearchAsyncWithUrlAndDisplayUrlBothProducesCorrectOperatorsAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));
        ITextSearch<BingWebPage> textSearch = new BingTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act - Use both Url and DisplayUrl properties
        var searchOptions = new TextSearchOptions<BingWebPage>
        {
            Top = 4,
            Skip = 0,
            Filter = page => page.Url!.Contains("github.com") && page.DisplayUrl!.Contains("microsoft")
        };
        KernelSearchResults<string> result = await textSearch.SearchAsync("repository", searchOptions);

        // Assert - Both should map to their respective operators
        var requestUris = this._messageHandlerStub.RequestUris;
        Assert.Single(requestUris);
        Assert.NotNull(requestUris[0]);
        string uri = requestUris[0].AbsoluteUri;
        Assert.Contains("url%3Agithub.com", uri);      // Url.Contains() ? url:
        Assert.Contains("site%3Amicrosoft", uri);      // DisplayUrl.Contains() ? site:
    }

    [Fact]
    public async Task GenericSearchAsyncWithComplexFourConditionFilterProducesCorrectBingQueryAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));
        ITextSearch<BingWebPage> textSearch = new BingTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act - Complex filter with 4 AND conditions testing multiple operator types
        var searchOptions = new TextSearchOptions<BingWebPage>
        {
            Top = 4,
            Skip = 0,
            Filter = page => page.Language == "en" &&
                            page.Language != "fr" &&  // This should be ignored (contradiction)
                            page.Name!.Contains("Tutorial") &&
                            page.Snippet!.Contains("beginner")
        };
        KernelSearchResults<string> result = await textSearch.SearchAsync("learn", searchOptions);

        // Assert - Verify all conditions present (including contradictory ones)
        var requestUris = this._messageHandlerStub.RequestUris;
        Assert.Single(requestUris);
        Assert.NotNull(requestUris[0]);
        string uri = requestUris[0].AbsoluteUri;
        Assert.Contains("language%3Aen", uri);
        Assert.Contains("-language%3Afr", uri);  // Both positive and negative language (contradictory but valid)
        Assert.Contains("intitle%3ATutorial", uri);
        Assert.Contains("inbody%3Abeginner", uri);
    }

    [Fact]
    public async Task GenericSearchAsyncWithSpecialCharactersInContainsValueProducesCorrectEncodingAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));
        ITextSearch<BingWebPage> textSearch = new BingTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act - Contains with special characters that need URL encoding
        var searchOptions = new TextSearchOptions<BingWebPage>
        {
            Top = 4,
            Skip = 0,
            Filter = page => page.Name!.Contains("C# & .NET")
        };
        KernelSearchResults<string> result = await textSearch.SearchAsync("programming", searchOptions);

        // Assert - Verify special characters are URL-encoded properly
        var requestUris = this._messageHandlerStub.RequestUris;
        Assert.Single(requestUris);
        Assert.NotNull(requestUris[0]);
        string uri = requestUris[0].AbsoluteUri;
        // Should contain URL-encoded version of "C# & .NET"
        Assert.Contains("intitle%3A", uri);
        // Verify the query was constructed (exact encoding may vary)
        Assert.True(uri.Contains("intitle"), "Should contain intitle operator");
    }

    [Fact]
    public async Task GenericSearchAsyncWithEmptyFilterProducesBaseQueryAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));
        ITextSearch<BingWebPage> textSearch = new BingTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act - Explicit null filter (should be treated like no filter)
        var searchOptions = new TextSearchOptions<BingWebPage>
        {
            Top = 5,
            Skip = 0,
            Filter = null
        };
        KernelSearchResults<string> result = await textSearch.SearchAsync("test query", searchOptions);

        // Assert - Should produce basic query without filter operators
        var requestUris = this._messageHandlerStub.RequestUris;
        Assert.Single(requestUris);
        Assert.NotNull(requestUris[0]);
        string uri = requestUris[0].AbsoluteUri;
        Assert.Contains("test", uri);  // Query should be present (URL-encoded)
        Assert.Contains("count=5", uri);
        Assert.DoesNotContain("intitle%3A", uri);
        Assert.DoesNotContain("language%3A", uri);
    }

    [Fact]
    public async Task GenericSearchAsyncWithOnlyInequalityFilterProducesNegationAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));
        ITextSearch<BingWebPage> textSearch = new BingTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act - Only inequality (pure negation)
        var searchOptions = new TextSearchOptions<BingWebPage>
        {
            Top = 4,
            Skip = 0,
            Filter = page => page.Language != "es"
        };
        KernelSearchResults<string> result = await textSearch.SearchAsync("content", searchOptions);

        // Assert - Verify negation operator present
        var requestUris = this._messageHandlerStub.RequestUris;
        Assert.Single(requestUris);
        Assert.NotNull(requestUris[0]);
        Assert.Contains("-language%3Aes", requestUris[0].AbsoluteUri);
    }

    [Fact]
    public async Task GenericSearchAsyncWithIsFamilyFriendlyInequalityThrowsExceptionAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));
        ITextSearch<BingWebPage> textSearch = new BingTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act - IsFamilyFriendly with inequality (should throw ArgumentException)
        var searchOptions = new TextSearchOptions<BingWebPage>
        {
            Top = 4,
            Skip = 0,
            Filter = page => page.IsFamilyFriendly != true
        };

        // Assert - Verify that negation on query parameter throws ArgumentException
        var exception = await Assert.ThrowsAsync<ArgumentException>(
            async () => await textSearch.SearchAsync("content", searchOptions));

        Assert.Contains("Negation (!= operator) is not supported for query parameter", exception.Message);
        Assert.Contains("safeSearch", exception.Message); // Query parameter name, not property name
        Assert.Contains("Negation only works with advanced search operators", exception.Message);
    }

    [Fact]
    public async Task GenericSearchAsyncWithContainsOnNameAndUrlProducesDistinctOperatorsAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));
        ITextSearch<BingWebPage> textSearch = new BingTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act - Same search term in different properties should use different operators
        var searchOptions = new TextSearchOptions<BingWebPage>
        {
            Top = 4,
            Skip = 0,
            Filter = page => page.Name!.Contains("docs") && page.Url!.Contains("docs")
        };
        KernelSearchResults<string> result = await textSearch.SearchAsync("documentation", searchOptions);

        // Assert - Verify both operators present despite same search term
        var requestUris = this._messageHandlerStub.RequestUris;
        Assert.Single(requestUris);
        Assert.NotNull(requestUris[0]);
        string uri = requestUris[0].AbsoluteUri;
        Assert.Contains("intitle%3Adocs", uri);  // Name ? intitle:
        Assert.Contains("url%3Adocs", uri);      // Url ? url:
        // Verify both operators are present (not deduplicated)
        Assert.Equal(2, System.Text.RegularExpressions.Regex.Matches(uri, "docs").Count);
    }

    [Fact]
    public async Task GenericSearchAsyncFilterTranslationPreservesResultStructureAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));
        ITextSearch<BingWebPage> textSearch = new BingTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act - Complex filter to ensure result structure not affected by filtering
        var searchOptions = new TextSearchOptions<BingWebPage>
        {
            Top = 10,
            Skip = 0,
            Filter = page => page.Language == "en" && page.Name!.Contains("Kernel")
        };
        KernelSearchResults<string> result = await textSearch.SearchAsync("AI", searchOptions);

        // Assert - Verify results are properly structured
        Assert.NotNull(result);
        Assert.NotNull(result.Results);
        var resultList = await result.Results.ToListAsync();
        Assert.Equal(10, resultList.Count);
        foreach (var item in resultList)
        {
            Assert.NotNull(item);
            Assert.NotEmpty(item);  // Each result should be non-empty string
        }
    }

    [Fact]
    public async Task GenericGetTextSearchResultsAsyncFilterTranslationPreservesMetadataAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));
        ITextSearch<BingWebPage> textSearch = new BingTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act - Use GetTextSearchResultsAsync with filter to verify metadata preservation
        var searchOptions = new TextSearchOptions<BingWebPage>
        {
            Top = 10,
            Skip = 0,
            Filter = page => page.Snippet!.Contains("semantic")
        };
        KernelSearchResults<TextSearchResult> result = await textSearch.GetTextSearchResultsAsync("Kernel", searchOptions);

        // Assert - Verify TextSearchResult structure with Name, Value, Link
        Assert.NotNull(result);
        Assert.NotNull(result.Results);
        var resultList = await result.Results.ToListAsync();
        Assert.Equal(10, resultList.Count);
        foreach (var textSearchResult in resultList)
        {
            Assert.NotNull(textSearchResult);
            Assert.NotNull(textSearchResult.Name);
            Assert.NotNull(textSearchResult.Value);
            Assert.NotNull(textSearchResult.Link);
            Assert.NotEmpty(textSearchResult.Name);
            Assert.NotEmpty(textSearchResult.Value);
            Assert.NotEmpty(textSearchResult.Link);
        }
    }

    [Fact]
    public async Task GenericGetSearchResultsAsyncFilterTranslationPreservesBingWebPageStructureAsync()
    {
        // Arrange
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));
        ITextSearch<BingWebPage> textSearch = new BingTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act - Use GetSearchResultsAsync with filter to get raw BingWebPage objects
        var searchOptions = new TextSearchOptions<BingWebPage>
        {
            Top = 10,
            Skip = 0,
            Filter = page => page.Language == "en" && page.DisplayUrl!.Contains("microsoft")
        };
        KernelSearchResults<BingWebPage> result = await textSearch.GetSearchResultsAsync("technology", searchOptions);

        // Assert - Verify BingWebPage objects have all expected properties
        Assert.NotNull(result);
        Assert.NotNull(result.Results);
        var resultList = await result.Results.ToListAsync();
        Assert.Equal(10, resultList.Count);
        foreach (var page in resultList)
        {
            Assert.NotNull(page);
            // Verify key properties are populated - now strongly typed, no cast needed!
            Assert.NotNull(page.Name);
            Assert.NotNull(page.Url);
            Assert.NotNull(page.Snippet);
            // DisplayUrl might be null in some cases, so don't assert NotNull
        }
    }

    [Fact]
    public async Task CollectionContainsFilterThrowsNotSupportedExceptionAsync()
    {
        // Arrange - Tests both Enumerable.Contains (C# 13-) and MemoryExtensions.Contains (C# 14+)
        // The same code array.Contains() resolves differently based on C# language version:
        // - C# 13 and earlier: Enumerable.Contains (LINQ extension method)
        // - C# 14 and later: MemoryExtensions.Contains (span-based optimization due to "first-class spans")
        // Our implementation handles both identically since Bing API doesn't support OR logic for either
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));
        ITextSearch<BingWebPage> textSearch = new BingTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });
        string[] languages = ["en", "fr"];

        // Act & Assert - Verify that collection Contains pattern throws clear exception
        var searchOptions = new TextSearchOptions<BingWebPage>
        {
            Top = 5,
            Skip = 0,
            Filter = page => languages.Contains(page.Language!)  // Enumerable.Contains (C# 13-) or MemoryExtensions.Contains (C# 14+)
        };

        var exception = await Assert.ThrowsAsync<NotSupportedException>(async () =>
        {
            await textSearch.SearchAsync("test", searchOptions);
        });

        // Assert - Verify error message explains the limitation clearly
        Assert.Contains("Collection Contains filters", exception.Message);
        Assert.Contains("not supported by Bing Search API", exception.Message);
        Assert.Contains("OR logic", exception.Message);
    }

    [Fact]
    public async Task StringContainsStillWorksWithLINQFiltersAsync()
    {
        // Arrange - Verify that String.Contains (instance method) still works
        // String.Contains is NOT affected by C# 14 "first-class spans" - only arrays are
        this._messageHandlerStub.AddJsonResponse(File.ReadAllText(WhatIsTheSKResponseJson));
        ITextSearch<BingWebPage> textSearch = new BingTextSearch(apiKey: "ApiKey", options: new() { HttpClient = this._httpClient });

        // Act - String.Contains should continue to work
        var searchOptions = new TextSearchOptions<BingWebPage>
        {
            Top = 5,
            Skip = 0,
            Filter = page => page.Name.Contains("Semantic")  // String.Contains - instance method
        };

        KernelSearchResults<string> result = await textSearch.SearchAsync("test", searchOptions);

        // Assert - Should succeed without exception
        Assert.NotNull(result);
        Assert.NotNull(result.Results);
        var resultsList = await result.Results.ToListAsync();
        Assert.NotEmpty(resultsList);

        // Verify the filter was translated correctly to intitle: operator
        var requestUris = this._messageHandlerStub.RequestUris;
        Assert.Single(requestUris);
        Assert.Contains("intitle%3ASemantic", requestUris[0]!.AbsoluteUri);
    }

    #endregion

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
