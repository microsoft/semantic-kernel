// Copyright (c) Microsoft. All rights reserved.
using System.Threading.Tasks;
using Examples;
using Microsoft.SemanticKernel.Search;
using Xunit;
using Xunit.Abstractions;

namespace Search;

/// <summary>
/// This example shows how to create and use a <see cref="ITextSearchService"/>.
/// </summary>
public sealed class GoogleSearch : BaseTest
{
    /// <summary>
    /// Show how to create a <see cref="ITextSearchService"/> and use it to perform a text search.
    /// </summary>
    [Fact]
    public async Task RunAsync()
    {
    }

    public GoogleSearch(ITestOutputHelper output) : base(output)
    {
    }
}
