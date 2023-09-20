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
        // Arrange
        IKernel kernel = Kernel.Builder.Build();

        // Act - Assert no exception occurs e.g. due to reflection
        kernel.ImportPlugin(new SearchUrlPlugin(), "search");
    }

    [Fact]
    public void AmazonSearchUrlSucceeds()
    {
        // Arrange
        var skill = new SearchUrlPlugin();

        // Act
        string actual = skill.AmazonSearchUrl(AnyInput);

        // Assert
        Assert.Equal($"https://www.amazon.com/s?k={this._encodedInput}", actual);
    }

    [Fact]
    public void BingSearchUrlSucceeds()
    {
        // Arrange
        var skill = new SearchUrlPlugin();

        // Act
        string actual = skill.BingSearchUrl(AnyInput);

        // Assert
        Assert.Equal($"https://www.bing.com/search?q={this._encodedInput}", actual);
    }

    [Fact]
    public void BingImagesSearchUrlSucceeds()
    {
        // Arrange
        var skill = new SearchUrlPlugin();

        // Act
        string actual = skill.BingImagesSearchUrl(AnyInput);

        // Assert
        Assert.Equal($"https://www.bing.com/images/search?q={this._encodedInput}", actual);
    }

    [Fact]
    public void BingMapsSearchUrl()
    {
        // Arrange
        var skill = new SearchUrlPlugin();

        // Act
        string actual = skill.BingMapsSearchUrl(AnyInput);

        // Assert
        Assert.Equal($"https://www.bing.com/maps?q={this._encodedInput}", actual);
    }

    [Fact]
    public void BingShoppingSearchUrl()
    {
        // Arrange
        var skill = new SearchUrlPlugin();

        // Act
        string actual = skill.BingShoppingSearchUrl(AnyInput);

        // Assert
        Assert.Equal($"https://www.bing.com/shop?q={this._encodedInput}", actual);
    }

    [Fact]
    public void BingNewsSearchUrl()
    {
        // Arrange
        var skill = new SearchUrlPlugin();

        // Act
        string actual = skill.BingNewsSearchUrl(AnyInput);

        // Assert
        Assert.Equal($"https://www.bing.com/news/search?q={this._encodedInput}", actual);
    }

    [Fact]
    public void BingTravelSearchUrl()
    {
        // Arrange
        var skill = new SearchUrlPlugin();

        // Act
        string actual = skill.BingTravelSearchUrl(AnyInput);

        // Assert
        Assert.Equal($"https://www.bing.com/travel/search?q={this._encodedInput}", actual);
    }

    [Fact]
    public void FacebookSearchUrl()
    {
        // Arrange
        var skill = new SearchUrlPlugin();

        // Act
        string actual = skill.FacebookSearchUrl(AnyInput);

        // Assert
        Assert.Equal($"https://www.facebook.com/search/top/?q={this._encodedInput}", actual);
    }

    [Fact]
    public void GitHubSearchUrl()
    {
        // Arrange
        var skill = new SearchUrlPlugin();

        // Act
        string actual = skill.GitHubSearchUrl(AnyInput);

        // Assert
        Assert.Equal($"https://github.com/search?q={this._encodedInput}", actual);
    }

    [Fact]
    public void LinkedInSearchUrl()
    {
        // Arrange
        var skill = new SearchUrlPlugin();

        // Act
        string actual = skill.LinkedInSearchUrl(AnyInput);

        // Assert
        Assert.Equal($"https://www.linkedin.com/search/results/index/?keywords={this._encodedInput}", actual);
    }

    [Fact]
    public void TwitterSearchUrl()
    {
        // Arrange
        var skill = new SearchUrlPlugin();

        // Act
        string actual = skill.TwitterSearchUrl(AnyInput);

        // Assert
        Assert.Equal($"https://twitter.com/search?q={this._encodedInput}", actual);
    }

    [Fact]
    public void WikipediaSearchUrl()
    {
        // Arrange
        var skill = new SearchUrlPlugin();

        // Act
        string actual = skill.WikipediaSearchUrl(AnyInput);

        // Assert
        Assert.Equal($"https://wikipedia.org/w/index.php?search={this._encodedInput}", actual);
    }
}
