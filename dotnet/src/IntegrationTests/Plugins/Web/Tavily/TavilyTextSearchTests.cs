// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Plugins.Web.Tavily;
using SemanticKernel.IntegrationTests.Data;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Plugins.Web.Tavily;

/// <summary>
/// Integration tests for <see cref="TavilyTextSearch"/>.
/// </summary>
public class TavilyTextSearchTests : BaseTextSearchTests
{
    /// <inheritdoc/>
    public override Task<ITextSearch> CreateTextSearchAsync()
    {
        var configuration = this.Configuration.GetSection("Tavily").Get<TavilyConfiguration>();
        Assert.NotNull(configuration);
        Assert.NotNull(configuration.ApiKey);

        return Task.FromResult<ITextSearch>(new TavilyTextSearch(apiKey: configuration.ApiKey));
    }

    /// <inheritdoc/>
    public override string GetQuery() => "What is the Semantic Kernel?";

    /// <inheritdoc/>
    public override TextSearchFilter GetTextSearchFilter() => new TextSearchFilter().Equality("include_domain", "devblogs.microsoft.com");

    /// <inheritdoc/>
    public override bool VerifySearchResults(object[] results, string query, TextSearchFilter? filter = null)
    {
        Assert.NotNull(results);
        Assert.NotEmpty(results);
        Assert.Equal(4, results.Length);
        foreach (var result in results)
        {
            Assert.NotNull(result);
            Assert.IsType<TavilySearchResult>(result);
        }

        return true;
    }
}
