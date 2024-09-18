// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Data;
using Xunit;

namespace SemanticKernel.UnitTests.Data;

#pragma warning disable xUnit1026 // Theory methods should use all of their parameters
public class TextSearchExtensionsTests
{
    private static MockTextSearch TextSearch => new();
    public static TheoryData<KernelPlugin> StandardPlugins => new()
        {
            { TextSearch.CreateWithSearch("SearchPlugin") },
            { TextSearch.CreateWithGetTextSearchResults("SearchPlugin") },
            { TextSearch.CreateWithGetSearchResults("SearchPlugin") },
        };
    public static TheoryData<KernelFunction, string> StandardFunctions => new()
        {
            { TextSearch.CreateSearch(), "Search" },
            { TextSearch.CreateGetTextSearchResults(), "GetTextSearchResults" },
            { TextSearch.CreateGetSearchResults(), "GetSearchResults" },
        };
    public static TheoryData<KernelFunction> CustomFunctions => new()
       {
            { TextSearch.CreateSearch(CustomSearchMethodOptions()) },
            { TextSearch.CreateGetTextSearchResults(CustomSearchMethodOptions()) },
            { TextSearch.CreateGetSearchResults(CustomSearchMethodOptions()) },
       };

    public static TheoryData<KernelFunction, int> FunctionsWithCount => new()
       {
            { TextSearch.CreateSearch(searchOptions: new() { Count = 10 }), 10 },
            { TextSearch.CreateGetTextSearchResults(searchOptions: new() { Count = 10 }), 10 },
            { TextSearch.CreateGetSearchResults(searchOptions: new() { Count = 10 }), 10 },
       };

    [Theory]
    [MemberData(nameof(StandardPlugins))]
    public void CreatePluginWorks(KernelPlugin plugin)
    {
        // Assert
        Assert.NotNull(plugin);
        Assert.Equal("SearchPlugin", plugin.Name);
        Assert.Equal(1, plugin.FunctionCount);
    }

    [Theory]
    [MemberData(nameof(StandardFunctions))]
    public void CreateFunctionWorks(KernelFunction function, string name)
    {
        // Assert
        Assert.NotNull(function);
        Assert.Equal(name, function.Name);
        Assert.Equal(3, function.Metadata.Parameters.Count);
        Assert.Equal("query", function.Metadata.Parameters[0].Name);
        Assert.Equal("count", function.Metadata.Parameters[1].Name);
        Assert.Equal("skip", function.Metadata.Parameters[2].Name);
    }

    [Theory]
    [MemberData(nameof(StandardFunctions))]
    public async Task FunctionReturnsEmptyWhenNoQueryAsync(KernelFunction function, string name)
    {
        // Act
        var result = await function.InvokeAsync(new());

        // Assert
        Assert.NotNull(result);
        var results = result.GetValue<IEnumerable<object>>();
        Assert.NotNull(results);
        Assert.Empty(results);
    }

    [Theory]
    [MemberData(nameof(StandardFunctions))]
    public async Task FunctionReturnsSuccessfullyAsync(KernelFunction function, string name)
    {
        // Act
        var result = await function.InvokeAsync(new(), new() { ["query"] = "What is the Semantic Kernel?" });

        // Assert
        Assert.NotNull(result);
        var results = result.GetValue<IEnumerable<object>>();
        Assert.NotNull(results);
        Assert.NotEmpty(results);
    }

    [Theory]
    [MemberData(nameof(CustomFunctions))]
    public void CreateCustomFunctionWorks(KernelFunction function)
    {
        // Assert
        Assert.NotNull(function);
        Assert.Equal("CustomSearch", function.Name);
        Assert.Equal(2, function.Metadata.Parameters.Count);
        Assert.Equal("query", function.Metadata.Parameters[0].Name);
        Assert.Equal("custom", function.Metadata.Parameters[1].Name);
    }

    [Theory]
    [MemberData(nameof(FunctionsWithCount))]
    public async Task FunctionWithCountReturnsCorrectResultsAsync(KernelFunction function, int count)
    {
        // Act
        var result = await function.InvokeAsync(new(), new() { ["query"] = "What is the Semantic Kernel?" });

        // Assert
        Assert.NotNull(result);
        var results = result.GetValue<IEnumerable<object>>();
        Assert.NotNull(results);
        Assert.NotEmpty(results);
        Assert.Equal(count, results.Count());
    }

    #region private
    /// <summary>
    /// Create the default <see cref="KernelFunctionFromMethodOptions"/> for <see cref="ITextSearch.SearchAsync(string, TextSearchOptions?, CancellationToken)"/>.
    /// </summary>
    private static KernelFunctionFromMethodOptions CustomSearchMethodOptions() =>
        new()
        {
            FunctionName = "CustomSearch",
            Description = "Perform a custom search for content related to the specified query",
            Parameters =
            [
                new KernelParameterMetadata("query") { Description = "What to search for", IsRequired = true },
                new KernelParameterMetadata("custom") { Description = "Some custom parameter", IsRequired = true },
            ],
            ReturnParameter = new() { ParameterType = typeof(KernelSearchResults<string>) },
        };
    #endregion
}
#pragma warning restore xUnit1026 // Theory methods should use all of their parameters
