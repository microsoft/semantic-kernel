// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Memory;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Memory;

/// <summary>
/// Contains tests for <see cref="TextRagComponent"/>
/// </summary>
public class TextRagComponentTests
{
    [Theory]
    [InlineData(null, null, "Consider the following source information when responding to the user:", "Include citations to the relevant information where it is referenced in the response.")]
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

        var options = new TextRagComponentOptions
        {
            SearchTime = TextRagComponentOptions.RagBehavior.BeforeAIInvoke,
            Top = 2,
            ContextPrompt = overrideContextPrompt,
            IncludeCitationsPrompt = overrideCitationsPrompt
        };

        var component = new TextRagComponent(mockTextSearch.Object, options);

        // Act
        var result = await component.OnModelInvokeAsync([new ChatMessage(ChatRole.User, "Sample user question?")], CancellationToken.None);

        // Assert
        Assert.Contains(expectedContextPrompt, result);
        Assert.Contains("Source Document Name: Doc1", result);
        Assert.Contains("Source Document Link: http://example.com/doc1", result);
        Assert.Contains("Source Document Contents: Content of Doc1", result);
        Assert.Contains("Source Document Name: Doc2", result);
        Assert.Contains("Source Document Link: http://example.com/doc2", result);
        Assert.Contains("Source Document Contents: Content of Doc2", result);
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
        var options = new TextRagComponentOptions
        {
            SearchTime = TextRagComponentOptions.RagBehavior.ViaPlugin,
            PluginFunctionName = overridePluginFunctionName,
            PluginFunctionDescription = overridePluginFunctionDescription
        };

        var component = new TextRagComponent(mockTextSearch.Object, options);

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
    [InlineData(null, null, "Consider the following source information when responding to the user:", "Include citations to the relevant information where it is referenced in the response.")]
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

        var options = new TextRagComponentOptions
        {
            ContextPrompt = overrideContextPrompt,
            IncludeCitationsPrompt = overrideCitationsPrompt
        };

        var component = new TextRagComponent(mockTextSearch.Object, options);

        // Act
        var result = await component.SearchAsync("Sample user question?", CancellationToken.None);

        // Assert
        Assert.Contains(expectedContextPrompt, result);
        Assert.Contains("Source Document Name: Doc1", result);
        Assert.Contains("Source Document Link: http://example.com/doc1", result);
        Assert.Contains("Source Document Contents: Content of Doc1", result);
        Assert.Contains("Source Document Name: Doc2", result);
        Assert.Contains("Source Document Link: http://example.com/doc2", result);
        Assert.Contains("Source Document Contents: Content of Doc2", result);
        Assert.Contains(expectedCitationsPrompt, result);
    }
}
