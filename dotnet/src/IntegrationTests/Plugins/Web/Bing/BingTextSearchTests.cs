// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Plugins.Web.Bing;
using SemanticKernel.IntegrationTests.Data;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Plugins.Web.Bing;

/// <summary>
/// Integration tests for <see cref="BingTextSearch"/>.
/// </summary>
public class BingTextSearchTests : BaseTextSearchTests
{
    /// <inheritdoc/>
    public override Task<ITextSearch> CreateTextSearchAsync()
    {
        var configuration = this.Configuration.GetSection("Bing").Get<BingConfiguration>();
        Assert.NotNull(configuration);
        Assert.NotNull(configuration.ApiKey);

        return Task.FromResult<ITextSearch>(new BingTextSearch(apiKey: configuration.ApiKey));
    }

    /// <inheritdoc/>
    public override string GetQuery() => "What is the Semantic Kernel?";

    /// <inheritdoc/>
    public override TextSearchFilter GetTextSearchFilter() => new TextSearchFilter().Equality("site", "devblogs.microsoft.com");

    /// <inheritdoc/>
    public override bool VerifySearchResult(object result, TextSearchFilter? filter = null) => result is BingWebPage;
}
