﻿// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Plugins.Web.Google;
using SemanticKernel.IntegrationTests.Data;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Plugins.Web.Google;
/// <summary>
/// Integration tests for <see cref="GoogleTextSearch"/>.
/// </summary>
public class GoogleTextSearchTests : BaseTextSearchTests
{
    /// <inheritdoc/>
    public override Task<ITextSearch> CreateTextSearchAsync()
    {
        var configuration = this.Configuration.GetSection("Google").Get<GoogleConfiguration>();
        Assert.NotNull(configuration);
        Assert.NotNull(configuration.ApiKey);
        Assert.NotNull(configuration.SearchEngineId);

        return Task.FromResult<ITextSearch>(new GoogleTextSearch(
            initializer: new() { ApiKey = configuration.ApiKey },
            searchEngineId: configuration.SearchEngineId));
    }

    /// <inheritdoc/>
    public override string GetQuery() => "What is the Semantic Kernel?";

    /// <inheritdoc/>
    public override TextSearchFilter GetTextSearchFilter() => new TextSearchFilter().Equality("siteSearch", "devblogs.microsoft.com");

    /// <inheritdoc/>
    public override bool VerifySearchResults(object[] results, string query, TextSearchFilter? filter = null)
    {
        Assert.NotNull(results);
        Assert.NotEmpty(results);
        Assert.Equal(4, results.Length);
        foreach (var result in results)
        {
            Assert.NotNull(result);
            Assert.IsType<global::Google.Apis.CustomSearchAPI.v1.Data.Result>(result);
        }

        return true;
    }
}
