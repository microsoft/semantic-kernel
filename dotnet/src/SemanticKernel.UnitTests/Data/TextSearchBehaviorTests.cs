// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel.Data;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Data;

/// <summary>
/// Contains tests for <see cref="TextSearchBehavior"/>
/// </summary>
public class TextSearchBehaviorTests
{
    [Theory]
    [InlineData(null, null, "Consider the following information when responding to the user:", "Include citations to the relevant information where it is referenced in the response.")]
    [InlineData("Custom context prompt", "Custom citations prompt", "Custom context prompt", "Custom citations prompt")]
    public async Task OnModelInvokeShouldIncludeSearchResultsInOutputAsync(
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

        var options = new TextSearchBehaviorOptions
        {
            SearchTime = TextSearchBehaviorOptions.RagBehavior.BeforeAIInvoke,
            Top = 2,
            ContextPrompt = overrideContextPrompt,
            IncludeCitationsPrompt = overrideCitationsPrompt
        };

        var component = new TextSearchBehavior(mockTextSearch.Object, options);

        // Act
        var result = await component.OnModelInvokeAsync([new ChatMessage(ChatRole.User, "Sample user question?")], CancellationToken.None);

        // Assert
        Assert.Contains(expectedContextPrompt, result);
        Assert.Contains("Item 1:", result);
        Assert.Contains("Name: Doc1", result);
        Assert.Contains("Link: http://example.com/doc1", result);
        Assert.Contains("Contents: Content of Doc1", result);
        Assert.Contains("Item 2:", result);
        Assert.Contains("Name: Doc2", result);
        Assert.Contains("Link: http://example.com/doc2", result);
        Assert.Contains("Contents: Content of Doc2", result);
        Assert.Contains(expectedCitationsPrompt, result);
    }

    [Theory]
    [InlineData(null, null, "Search", "Allows searching for additional information to help answer the user question.")]
    [InlineData("CustomSearch", "CustomDescription", "CustomSearch", "CustomDescription")]
    public void AIFunctionsShouldBeRegisteredCorrectly(
        string? overridePluginFunctionName,
        string? overridePluginFunctionDescription,
        string expectedPluginFunctionName,
        string expectedPluginFunctionDescription)
    {
        // Arrange
        var mockTextSearch = new Mock<ITextSearch>();
        var options = new TextSearchBehaviorOptions
        {
            SearchTime = TextSearchBehaviorOptions.RagBehavior.ViaPlugin,
            PluginFunctionName = overridePluginFunctionName,
            PluginFunctionDescription = overridePluginFunctionDescription
        };

        var component = new TextSearchBehavior(mockTextSearch.Object, options);

        // Act
        var aiFunctions = component.AIFunctions;

        // Assert
        Assert.NotNull(aiFunctions);
        Assert.Single(aiFunctions);
        var aiFunction = aiFunctions.First();
        Assert.Equal(expectedPluginFunctionName, aiFunction.Name);
        Assert.Equal(expectedPluginFunctionDescription, aiFunction.Description);
    }

    [Theory]
    [InlineData(null, null, "Consider the following information when responding to the user:", "Include citations to the relevant information where it is referenced in the response.")]
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

        var options = new TextSearchBehaviorOptions
        {
            ContextPrompt = overrideContextPrompt,
            IncludeCitationsPrompt = overrideCitationsPrompt
        };

        var component = new TextSearchBehavior(mockTextSearch.Object, options);

        // Act
        var result = await component.SearchAsync("Sample user question?", CancellationToken.None);

        // Assert
        Assert.Contains(expectedContextPrompt, result);
        Assert.Contains("Item 1:", result);
        Assert.Contains("Name: Doc1", result);
        Assert.Contains("Link: http://example.com/doc1", result);
        Assert.Contains("Contents: Content of Doc1", result);
        Assert.Contains("Item 2:", result);
        Assert.Contains("Name: Doc2", result);
        Assert.Contains("Link: http://example.com/doc2", result);
        Assert.Contains("Contents: Content of Doc2", result);
        Assert.Contains(expectedCitationsPrompt, result);
    }

    [Fact]
    public async Task OnModelInvokeShouldUseOverrideContextFormatterIfProvidedAsync()
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

        var customFormatter = new TextSearchBehaviorOptions.ContextFormatterType(results =>
            $"Custom formatted context with {results.Count} results.");

        var options = new TextSearchBehaviorOptions
        {
            SearchTime = TextSearchBehaviorOptions.RagBehavior.BeforeAIInvoke,
            Top = 2,
            ContextFormatter = customFormatter
        };

        var component = new TextSearchBehavior(mockTextSearch.Object, options);

        // Act
        var result = await component.OnModelInvokeAsync([new ChatMessage(ChatRole.User, "Sample user question?")], CancellationToken.None);

        // Assert
        Assert.Equal("Custom formatted context with 2 results.", result);
    }
}
