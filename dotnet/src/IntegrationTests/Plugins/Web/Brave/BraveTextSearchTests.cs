// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Plugins.Web.Brave;
using SemanticKernel.IntegrationTests.Data;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Plugins.Web.Brave;

/// <summary>
/// Integration tests for <see cref="BraveTextSearch"/>.
/// </summary>
public class BraveTextSearchTests : BaseTextSearchTests
{
    /// <inheritdoc/>
    public override Task<ITextSearch> CreateTextSearchAsync()
    {
        var configuration = this.Configuration.GetSection("Brave").Get<BraveConfiguration>();
        Assert.NotNull(configuration);
        Assert.NotNull(configuration.ApiKey);

        return Task.FromResult<ITextSearch>(new BraveTextSearch(apiKey: configuration.ApiKey));
    }

    /// <inheritdoc/>
    public override string GetQuery() => "What is the Semantic Kernel?";

    /// <inheritdoc/>
    public override TextSearchFilter GetTextSearchFilter() => new TextSearchFilter().Equality("search_lang", "de");

    /// <inheritdoc/>
    public override bool VerifySearchResults(object[] results, string query, TextSearchFilter? filter = null)
    {
        Assert.NotNull(results);
        Assert.NotEmpty(results);
        Assert.Equal(4, results.Length);
        foreach (var result in results)
        {
            Assert.NotNull(result);
            Assert.IsType<BraveWebResult>(result);
        }

        return true;
    }
}
