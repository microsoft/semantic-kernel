// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Encodings.Web;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.Web;
using Xunit;

namespace SemanticKernel.Plugins.UnitTests.Web;

public class SearchUrlPluginTests
{
    private const string AnyInput = "<something to search for>";
    private readonly string _encodedInput = Uri.EscapeDataString(AnyInput); // CHANGED: Use Uri.EscapeDataString

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

    // NEW SECURITY TESTS ADDED
    [Fact]
    public void AmazonSearchUrl_ThrowsOnNullQuery()
    {
        // Arrange
        var plugin = new SearchUrlPlugin();

        // Act & Assert
        Assert.Throws<ArgumentException>(() => plugin.AmazonSearchUrl(null!));
    }

    [Fact]
    public void AmazonSearchUrl_ThrowsOnEmptyQuery()
    {
        // Arrange
        var plugin = new SearchUrlPlugin();

        // Act & Assert
        Assert.Throws<ArgumentException>(() => plugin.AmazonSearchUrl(""));
    }

    [Fact]
    public void AmazonSearchUrl_ThrowsOnWhitespaceQuery()
    {
        // Arrange
        var plugin = new SearchUrlPlugin();

        // Act & Assert
        Assert.Throws<ArgumentException>(() => plugin.AmazonSearchUrl("   "));
    }

    [Fact]
    public void AmazonSearchUrl_ThrowsOnVeryLongQuery()
    {
        // Arrange
        var plugin = new SearchUrlPlugin();
        var longQuery = new string('a', 3000); // Exceeds 2048 limit

        // Act & Assert
        Assert.Throws<ArgumentException>(() => plugin.AmazonSearchUrl(longQuery));
    }

    [Fact]
    public void AmazonSearchUrl_ThrowsOnProtocolInjection()
    {
        // Arrange
        var plugin = new SearchUrlPlugin();

        // Act & Assert
        Assert.Throws<ArgumentException>(() => plugin.AmazonSearchUrl("http://evil.com"));
        Assert.Throws<ArgumentException>(() => plugin.AmazonSearchUrl("javascript:alert(1)"));
        Assert.Throws<ArgumentException>(() => plugin.AmazonSearchUrl("data:text/html,<script>alert(1)</script>"));
    }

    [Theory]
    [InlineData("search&sort=price")]
    [InlineData("price<100")]
    [InlineData("test#fragment")]
    [InlineData("query?param=value")]
    [InlineData("path/traversal")]
    [InlineData("unicode😀test")]
    [InlineData("test with spaces")]
    [InlineData("test+plus")]
    public void AmazonSearchUrl_ProperlyEncodesSpecialCharacters(string query)
    {
        // Arrange
        var plugin = new SearchUrlPlugin();
        var expectedEncoded = Uri.EscapeDataString(query);

        // Act
        var result = plugin.AmazonSearchUrl(query);

        // Assert
        Assert.Equal($"https://www.amazon.com/s?k={expectedEncoded}", result);
    }

    [Fact]
    public void UrlEncoding_ComparisonTest()
    {
        // This test demonstrates the difference between the old and new encoding
        string[] testCases = new[]
        {
            "search&sort=price",
            "test with spaces",
            "c++ programming",
            "price<100>200",
            "test#section",
            "query?param=value",
            "path/traversal",
            "user@domain",
            "percent%20encoded",
            "unicode😀emoji"
        };

        foreach (var testCase in testCases)
        {
            var oldEncoding = UrlEncoder.Default.Encode(testCase);
            var newEncoding = Uri.EscapeDataString(testCase);
            
            // They should be different in some cases
            Console.WriteLine($"Input: '{testCase}'");
            Console.WriteLine($"  Old (UrlEncoder): '{oldEncoding}'");
            Console.WriteLine($"  New (EscapeDataString): '{newEncoding}'");
            Console.WriteLine($"  Same: {oldEncoding == newEncoding}");
            Console.WriteLine();
        }
    }

    [Fact]
    public void AllMethods_ConsistentBehavior()
    {
        // Test that all methods use the same encoding
        var plugin = new SearchUrlPlugin();
        var testQuery = "test&query=value";
        var expectedEncoded = Uri.EscapeDataString(testQuery);

        var methods = new (string methodName, Func<string> getResult)[]
        {
            ("AmazonSearchUrl", () => plugin.AmazonSearchUrl(testQuery)),
            ("BingSearchUrl", () => plugin.BingSearchUrl(testQuery)),
            ("BingImagesSearchUrl", () => plugin.BingImagesSearchUrl(testQuery)),
            ("BingMapsSearchUrl", () => plugin.BingMapsSearchUrl(testQuery)),
            ("BingShoppingSearchUrl", () => plugin.BingShoppingSearchUrl(testQuery)),
            ("BingNewsSearchUrl", () => plugin.BingNewsSearchUrl(testQuery)),
            ("BingTravelSearchUrl", () => plugin.BingTravelSearchUrl(testQuery)),
            ("BraveSearchUrl", () => plugin.BraveSearchUrl(testQuery)),
            ("BraveImagesSearchUrl", () => plugin.BraveImagesSearchUrl(testQuery)),
            ("BraveNewsSearchUrl", () => plugin.BraveNewsSearchUrl(testQuery)),
            ("BraveGooglesSearchUrl", () => plugin.BraveGooglesSearchUrl(testQuery)),
            ("BraveVideosSearchUrl", () => plugin.BraveVideosSearchUrl(testQuery)),
            ("FacebookSearchUrl", () => plugin.FacebookSearchUrl(testQuery)),
            ("GitHubSearchUrl", () => plugin.GitHubSearchUrl(testQuery)),
            ("LinkedInSearchUrl", () => plugin.LinkedInSearchUrl(testQuery)),
            ("TwitterSearchUrl", () => plugin.TwitterSearchUrl(testQuery)),
            ("WikipediaSearchUrl", () => plugin.WikipediaSearchUrl(testQuery))
        };

        foreach (var method in methods)
        {
            var result = method.getResult();
            Assert.Contains(expectedEncoded, result);
            
            // Verify no unencoded special characters in the encoded part
            var baseUrl = result.Split('=')[0] + "=";
            var encodedPart = result.Substring(baseUrl.Length);
            Assert.DoesNotContain("&", encodedPart);
            Assert.DoesNotContain("<", encodedPart);
            Assert.DoesNotContain(">", encodedPart);
            Assert.DoesNotContain("#", encodedPart);
            Assert.DoesNotContain("?", encodedPart);
        }
    }
}
