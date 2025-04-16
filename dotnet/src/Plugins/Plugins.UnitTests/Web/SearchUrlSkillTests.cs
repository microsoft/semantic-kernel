// Copyright (c) Microsoft. All rights reserved.

using System.Text.Encodings.Web;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.Web;
using Xunit;

namespace SemanticKernel.Plugins.UnitTests.Web;

public class SearchUrlPluginTests
{
    private const string AnyInput = "<something to search for>";
    private readonly string _encodedInput = UrlEncoder.Default.Encode(AnyInput);

    [Fact]
    public void ItCanBeInstantiated()
    {
        // Act - Assert no exception occurs
        var _ = new SearchUrlPlugin();
    }

    [Fact]
    public void ItCanBeImported()
    {
        // Act - Assert no exception occurs e.g. due to reflection
        Assert.NotNull(KernelPluginFactory.CreateFromType<SearchUrlPlugin>("search"));
    }

    [Fact]
    public void AmazonSearchUrlSucceeds()
    {
        // Arrange
        var plugin = new SearchUrlPlugin();

        // Act
        string actual = plugin.AmazonSearchUrl(AnyInput);

        // Assert
        Assert.Equal($"https://www.amazon.com/s?k={this._encodedInput}", actual);
    }

    [Fact]
    public void BingSearchUrlSucceeds()
    {
        // Arrange
        var plugin = new SearchUrlPlugin();

        // Act
        string actual = plugin.BingSearchUrl(AnyInput);

        // Assert
        Assert.Equal($"https://www.bing.com/search?q={this._encodedInput}", actual);
    }

    [Fact]
    public void BingImagesSearchUrlSucceeds()
    {
        // Arrange
        var plugin = new SearchUrlPlugin();

        // Act
        string actual = plugin.BingImagesSearchUrl(AnyInput);

        // Assert
        Assert.Equal($"https://www.bing.com/images/search?q={this._encodedInput}", actual);
    }

    [Fact]
    public void BingMapsSearchUrl()
    {
        // Arrange
        var plugin = new SearchUrlPlugin();

        // Act
        string actual = plugin.BingMapsSearchUrl(AnyInput);

        // Assert
        Assert.Equal($"https://www.bing.com/maps?q={this._encodedInput}", actual);
    }

    [Fact]
    public void BingShoppingSearchUrl()
    {
        // Arrange
        var plugin = new SearchUrlPlugin();

        // Act
        string actual = plugin.BingShoppingSearchUrl(AnyInput);

        // Assert
        Assert.Equal($"https://www.bing.com/shop?q={this._encodedInput}", actual);
    }

    [Fact]
    public void BingNewsSearchUrl()
    {
        // Arrange
        var plugin = new SearchUrlPlugin();

        // Act
        string actual = plugin.BingNewsSearchUrl(AnyInput);

        // Assert
        Assert.Equal($"https://www.bing.com/news/search?q={this._encodedInput}", actual);
    }

    [Fact]
    public void BingTravelSearchUrl()
    {
        // Arrange
        var plugin = new SearchUrlPlugin();

        // Act
        string actual = plugin.BingTravelSearchUrl(AnyInput);

        // Assert
        Assert.Equal($"https://www.bing.com/travel/search?q={this._encodedInput}", actual);
    }

    [Fact]
    public void BraveSearchUrl()
    {
        // Arrange
        var plugin = new SearchUrlPlugin();

        // Act
        string actual = plugin.BraveSearchUrl(AnyInput);

        // Assert
        Assert.Equal($"https://search.brave.com/search?q={this._encodedInput}", actual);
    }

    [Fact]
    public void BraveImagesSearchUrl()
    {
        // Arrange
        var plugin = new SearchUrlPlugin();

        // Act
        string actual = plugin.BraveImagesSearchUrl(AnyInput);

        // Assert
        Assert.Equal($"https://search.brave.com/images?q={this._encodedInput}", actual);
    }

    [Fact]
    public void BraveNewsSearchUrl()
    {
        // Arrange
        var plugin = new SearchUrlPlugin();

        // Act
        string actual = plugin.BraveNewsSearchUrl(AnyInput);

        // Assert
        Assert.Equal($"https://search.brave.com/news?q={this._encodedInput}", actual);
    }

    [Fact]
    public void BraveGooglesSearchUrl()
    {
        // Arrange
        var plugin = new SearchUrlPlugin();

        // Act
        string actual = plugin.BraveGooglesSearchUrl(AnyInput);

        // Assert
        Assert.Equal($"https://search.brave.com/goggles?q={this._encodedInput}", actual);
    }

    [Fact]
    public void BraveVideosSearchUrl()
    {
        // Arrange
        var plugin = new SearchUrlPlugin();

        // Act
        string actual = plugin.BraveVideosSearchUrl(AnyInput);

        // Assert
        Assert.Equal($"https://search.brave.com/videos?q={this._encodedInput}", actual);
    }

    [Fact]
    public void FacebookSearchUrl()
    {
        // Arrange
        var plugin = new SearchUrlPlugin();

        // Act
        string actual = plugin.FacebookSearchUrl(AnyInput);

        // Assert
        Assert.Equal($"https://www.facebook.com/search/top/?q={this._encodedInput}", actual);
    }

    [Fact]
    public void GitHubSearchUrl()
    {
        // Arrange
        var plugin = new SearchUrlPlugin();

        // Act
        string actual = plugin.GitHubSearchUrl(AnyInput);

        // Assert
        Assert.Equal($"https://github.com/search?q={this._encodedInput}", actual);
    }

    [Fact]
    public void LinkedInSearchUrl()
    {
        // Arrange
        var plugin = new SearchUrlPlugin();

        // Act
        string actual = plugin.LinkedInSearchUrl(AnyInput);

        // Assert
        Assert.Equal($"https://www.linkedin.com/search/results/index/?keywords={this._encodedInput}", actual);
    }

    [Fact]
    public void TwitterSearchUrl()
    {
        // Arrange
        var plugin = new SearchUrlPlugin();

        // Act
        string actual = plugin.TwitterSearchUrl(AnyInput);

        // Assert
        Assert.Equal($"https://twitter.com/search?q={this._encodedInput}", actual);
    }

    [Fact]
    public void WikipediaSearchUrl()
    {
        // Arrange
        var plugin = new SearchUrlPlugin();

        // Act
        string actual = plugin.WikipediaSearchUrl(AnyInput);

        // Assert
        Assert.Equal($"https://wikipedia.org/w/index.php?search={this._encodedInput}", actual);
    }
}
