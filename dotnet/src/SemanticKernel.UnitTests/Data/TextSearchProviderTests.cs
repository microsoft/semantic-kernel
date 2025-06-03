// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Data;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Data;

/// <summary>
/// Contains tests for <see cref="TextSearchProvider"/>
/// </summary>
public class TextSearchProviderTests
{
    private readonly Mock<ILogger<TextSearchProvider>> _loggerMock;
    private readonly Mock<ILoggerFactory> _loggerFactoryMock;

    public TextSearchProviderTests()
    {
        this._loggerMock = new();
        this._loggerFactoryMock = new();
        this._loggerFactoryMock
            .Setup(f => f.CreateLogger(It.IsAny<string>()))
            .Returns(this._loggerMock.Object);
        this._loggerFactoryMock
            .Setup(f => f.CreateLogger(typeof(TextSearchProvider).FullName!))
            .Returns(this._loggerMock.Object);
    }

    [Theory]
    [InlineData(null, null, "Consider the following information from source documents when responding to the user:", "Include citations to the source document with document name and link if document name and link is available.", true)]
    [InlineData("Custom context prompt", "Custom citations prompt", "Custom context prompt", "Custom citations prompt", false)]
    public async Task ModelInvokingShouldIncludeSearchResultsInOutputAsync(
        string? overrideContextPrompt,
        string? overrideCitationsPrompt,
        string expectedContextPrompt,
        string expectedCitationsPrompt,
        bool withLogging)
    {
        // Arrange
        var mockTextSearch = new Mock<ITextSearch>();
        var searchResults = new Mock<IAsyncEnumerable<TextSearchResult>>();
        var mockEnumerator = new Mock<IAsyncEnumerator<TextSearchResult>>();

        // Mock search results
        var results = new List<TextSearchResult>
        {
            new("Content of Doc1") { Name = "Doc1", Link = "http://example.com/doc1" },
            new("Content of Doc2") { Name = "Doc2", Link = "http://example.com/doc2" }
        };

        mockEnumerator.SetupSequence(e => e.MoveNextAsync())
            .ReturnsAsync(true)
            .ReturnsAsync(true)
            .ReturnsAsync(false);

        mockEnumerator.SetupSequence(e => e.Current)
            .Returns(results[0])
            .Returns(results[1]);

        searchResults.Setup(r => r.GetAsyncEnumerator(It.IsAny<CancellationToken>()))
            .Returns(mockEnumerator.Object);

        mockTextSearch.Setup(ts => ts.GetTextSearchResultsAsync(
            It.IsAny<string>(),
            It.IsAny<TextSearchOptions>(),
            It.IsAny<CancellationToken>()))
            .ReturnsAsync(new KernelSearchResults<TextSearchResult>(searchResults.Object));

        var options = new TextSearchProviderOptions
        {
            SearchTime = TextSearchProviderOptions.RagBehavior.BeforeAIInvoke,
            Top = 2,
            ContextPrompt = overrideContextPrompt,
            IncludeCitationsPrompt = overrideCitationsPrompt
        };

        var component = new TextSearchProvider(
            mockTextSearch.Object,
            withLogging ? this._loggerFactoryMock.Object : null,
            options: options);

        // Act
        var result = await component.ModelInvokingAsync([new ChatMessage(ChatRole.User, "Sample user question?")], CancellationToken.None);

        // Assert
        Assert.Contains(expectedContextPrompt, result.Instructions);
        Assert.Contains("SourceDocName: Doc1", result.Instructions);
        Assert.Contains("SourceDocLink: http://example.com/doc1", result.Instructions);
        Assert.Contains("Contents: Content of Doc1", result.Instructions);
        Assert.Contains("SourceDocName: Doc2", result.Instructions);
        Assert.Contains("SourceDocLink: http://example.com/doc2", result.Instructions);
        Assert.Contains("Contents: Content of Doc2", result.Instructions);
        Assert.Contains(expectedCitationsPrompt, result.Instructions);

        if (withLogging)
        {
            this._loggerMock.Verify(
                l => l.Log(
                    LogLevel.Information,
                    It.IsAny<EventId>(),
                    It.Is<It.IsAnyType>((v, t) => v.ToString()!.Contains("TextSearchBehavior: Retrieved 2 search results.")),
                    It.IsAny<Exception?>(),
                    It.IsAny<Func<It.IsAnyType, Exception?, string>>()),
                Times.AtLeastOnce);

            this._loggerMock.Verify(
                l => l.Log(
                    LogLevel.Trace,
                    It.IsAny<EventId>(),
                    It.Is<It.IsAnyType>((v, t) => v.ToString()!.Contains("TextSearchBehavior:\nInput Messages:Sample user question?\nOutput context instructions:") && v.ToString()!.Contains("SourceDocName: Doc1") && v.ToString()!.Contains("SourceDocName: Doc2")),
                    It.IsAny<Exception?>(),
                    It.IsAny<Func<It.IsAnyType, Exception?, string>>()),
                Times.AtLeastOnce);
        }
    }

    [Theory]
    [InlineData(null, null, "Search", "Allows searching for additional information to help answer the user question.")]
    [InlineData("CustomSearch", "CustomDescription", "CustomSearch", "CustomDescription")]
    public async Task AIFunctionsShouldBeRegisteredCorrectly(
        string? overridePluginFunctionName,
        string? overridePluginFunctionDescription,
        string expectedPluginFunctionName,
        string expectedPluginFunctionDescription)
    {
        // Arrange
        var mockTextSearch = new Mock<ITextSearch>();
        var options = new TextSearchProviderOptions
        {
            SearchTime = TextSearchProviderOptions.RagBehavior.OnDemandFunctionCalling,
            PluginFunctionName = overridePluginFunctionName,
            PluginFunctionDescription = overridePluginFunctionDescription
        };

        var component = new TextSearchProvider(mockTextSearch.Object, options: options);

        // Act
        var aiContextAdditions = await component.ModelInvokingAsync([new ChatMessage(ChatRole.User, "Sample user question?")], CancellationToken.None);

        // Assert
        var aiFunctions = aiContextAdditions.AIFunctions;
        Assert.NotNull(aiFunctions);
        Assert.Single(aiFunctions);
        var aiFunction = aiFunctions.First();
        Assert.Equal(expectedPluginFunctionName, aiFunction.Name);
        Assert.Equal(expectedPluginFunctionDescription, aiFunction.Description);
    }

    [Theory]
    [InlineData(null, null, "Consider the following information from source documents when responding to the user:", "Include citations to the source document with document name and link if document name and link is available.")]
    [InlineData("Custom context prompt", "Custom citations prompt", "Custom context prompt", "Custom citations prompt")]
    public async Task SearchAsyncShouldIncludeSearchResultsInOutputAsync(
        string? overrideContextPrompt,
        string? overrideCitationsPrompt,
        string expectedContextPrompt,
        string expectedCitationsPrompt)

    {
        // Arrange
        var mockTextSearch = new Mock<ITextSearch>();
        var searchResults = new Mock<IAsyncEnumerable<TextSearchResult>>();
        var mockEnumerator = new Mock<IAsyncEnumerator<TextSearchResult>>();

        // Mock search results
        var results = new List<TextSearchResult>
        {
            new("Content of Doc1") { Name = "Doc1", Link = "http://example.com/doc1" },
            new("Content of Doc2") { Name = "Doc2", Link = "http://example.com/doc2" }
        };

        mockEnumerator.SetupSequence(e => e.MoveNextAsync())
            .ReturnsAsync(true)
            .ReturnsAsync(true)
            .ReturnsAsync(false);

        mockEnumerator.SetupSequence(e => e.Current)
            .Returns(results[0])
            .Returns(results[1]);

        searchResults.Setup(r => r.GetAsyncEnumerator(It.IsAny<CancellationToken>()))
            .Returns(mockEnumerator.Object);

        mockTextSearch.Setup(ts => ts.GetTextSearchResultsAsync(
            It.IsAny<string>(),
            It.IsAny<TextSearchOptions>(),
            It.IsAny<CancellationToken>()))
            .ReturnsAsync(new KernelSearchResults<TextSearchResult>(searchResults.Object));

        var options = new TextSearchProviderOptions
        {
            ContextPrompt = overrideContextPrompt,
            IncludeCitationsPrompt = overrideCitationsPrompt
        };

        var component = new TextSearchProvider(mockTextSearch.Object, options: options);

        // Act
        var result = await component.SearchAsync("Sample user question?", CancellationToken.None);

        // Assert
        Assert.Contains(expectedContextPrompt, result);
        Assert.Contains("SourceDocName: Doc1", result);
        Assert.Contains("SourceDocLink: http://example.com/doc1", result);
        Assert.Contains("Contents: Content of Doc1", result);
        Assert.Contains("SourceDocName: Doc2", result);
        Assert.Contains("SourceDocLink: http://example.com/doc2", result);
        Assert.Contains("Contents: Content of Doc2", result);
        Assert.Contains(expectedCitationsPrompt, result);
    }

    [Fact]
    public async Task ModelInvokingShouldUseOverrideContextFormatterIfProvidedAsync()
    {
        // Arrange
        var mockTextSearch = new Mock<ITextSearch>();
        var searchResults = new Mock<IAsyncEnumerable<TextSearchResult>>();
        var mockEnumerator = new Mock<IAsyncEnumerator<TextSearchResult>>();

        // Mock search results
        var results = new List<TextSearchResult>
        {
            new("Content of Doc1") { Name = "Doc1", Link = "http://example.com/doc1" },
            new("Content of Doc2") { Name = "Doc2", Link = "http://example.com/doc2" }
        };

        mockEnumerator.SetupSequence(e => e.MoveNextAsync())
            .ReturnsAsync(true)
            .ReturnsAsync(true)
            .ReturnsAsync(false);

        mockEnumerator.SetupSequence(e => e.Current)
            .Returns(results[0])
            .Returns(results[1]);

        searchResults.Setup(r => r.GetAsyncEnumerator(It.IsAny<CancellationToken>()))
            .Returns(mockEnumerator.Object);

        mockTextSearch.Setup(ts => ts.GetTextSearchResultsAsync(
            It.IsAny<string>(),
            It.IsAny<TextSearchOptions>(),
            It.IsAny<CancellationToken>()))
            .ReturnsAsync(new KernelSearchResults<TextSearchResult>(searchResults.Object));

        var options = new TextSearchProviderOptions
        {
            SearchTime = TextSearchProviderOptions.RagBehavior.BeforeAIInvoke,
            Top = 2,
            ContextFormatter = results => $"Custom formatted context with {results.Count} results."
        };

        var component = new TextSearchProvider(mockTextSearch.Object, options: options);

        // Act
        var result = await component.ModelInvokingAsync([new ChatMessage(ChatRole.User, "Sample user question?")], CancellationToken.None);

        // Assert
        Assert.Equal("Custom formatted context with 2 results.", result.Instructions);
    }
}
