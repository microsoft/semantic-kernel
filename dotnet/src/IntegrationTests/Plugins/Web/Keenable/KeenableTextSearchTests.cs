// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable CS0618 // ITextSearch is obsolete

using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Plugins.Web.Keenable;
using SemanticKernel.IntegrationTests.Data;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Plugins.Web.Keenable;

/// <summary>
/// Integration tests for <see cref="KeenableTextSearch"/>.
/// </summary>
public class KeenableTextSearchTests : BaseTextSearchTests
{
    /// <inheritdoc/>
    public override Task<ITextSearch> CreateTextSearchAsync()
    {
        // The API key is optional; without a "Keenable" section the public endpoint is used.
        var configuration = this.Configuration.GetSection("Keenable").Get<KeenableConfiguration>();

        return Task.FromResult<ITextSearch>(new KeenableTextSearch(apiKey: configuration?.ApiKey));
    }

    /// <inheritdoc/>
    public override string GetQuery() => "What is the Semantic Kernel?";

    /// <inheritdoc/>
    public override TextSearchFilter GetTextSearchFilter() => new TextSearchFilter().Equality("site", "learn.microsoft.com");

    /// <inheritdoc/>
    public override bool VerifySearchResults(object[] results, string query, TextSearchFilter? filter = null)
    {
        Assert.NotNull(results);
        Assert.NotEmpty(results);
        Assert.Equal(4, results.Length);
        foreach (var result in results)
        {
            Assert.NotNull(result);
            var searchResult = Assert.IsType<KeenableSearchResult>(result);
            Assert.NotEmpty(searchResult.Url);
            if (filter is not null)
            {
                Assert.StartsWith("https://learn.microsoft.com/", searchResult.Url, System.StringComparison.Ordinal);
            }
        }

        return true;
    }
}
