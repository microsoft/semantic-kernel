// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Data;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using SemanticKernel.AotTests.JsonSerializerContexts;
using SemanticKernel.AotTests.Plugins;

namespace SemanticKernel.AotTests.UnitTests.Search;

internal sealed class TextSearchExtensionsTests
{
    private static readonly JsonSerializerOptions s_jsonSerializerOptions = new()
    {
        TypeInfoResolverChain = { CustomResultJsonSerializerContext.Default }
    };

    public static async Task CreateWithSearch()
    {
        // Arrange
        var testData = new List<string> { "test-value" };
        KernelSearchResults<string> results = new(testData.ToAsyncEnumerable());
#pragma warning disable CS0618 // Type or member is obsolete
        ITextSearch textSearch = new MockTextSearch(results);
#pragma warning restore CS0618 // Type or member is obsolete

        // Act
        var plugin = textSearch.CreateWithSearch("SearchPlugin", s_jsonSerializerOptions);

        // Assert
        await AssertSearchFunctionSchemaAndInvocationResult<string>(plugin["Search"], testData[0]);
    }

    public static async Task CreateWithGetTextSearchResults()
    {
        // Arrange
        var testData = new List<TextSearchResult> { new("test-value") };
        KernelSearchResults<TextSearchResult> results = new(testData.ToAsyncEnumerable());
#pragma warning disable CS0618 // Type or member is obsolete
        ITextSearch textSearch = new MockTextSearch(results);
#pragma warning restore CS0618 // Type or member is obsolete

        // Act
        var plugin = textSearch.CreateWithGetTextSearchResults("SearchPlugin", s_jsonSerializerOptions);

        // Assert
        await AssertSearchFunctionSchemaAndInvocationResult<TextSearchResult>(plugin["GetTextSearchResults"], testData[0]);
    }

    public static async Task CreateWithGetSearchResults()
    {
        // Arrange
        var testData = new List<CustomResult> { new("test-value") };
        KernelSearchResults<object> results = new(testData.ToAsyncEnumerable());
#pragma warning disable CS0618 // Type or member is obsolete
        ITextSearch textSearch = new MockTextSearch(results);
#pragma warning restore CS0618 // Type or member is obsolete

        // Act
        var plugin = textSearch.CreateWithGetSearchResults("SearchPlugin", s_jsonSerializerOptions);

        // Assert
        await AssertSearchFunctionSchemaAndInvocationResult<object>(plugin["GetSearchResults"], testData[0]);
    }

    #region assert
    internal static async Task AssertSearchFunctionSchemaAndInvocationResult<T>(KernelFunction function, T expectedResult)
    {
        // Assert input parameter schema  
        AssertSearchFunctionMetadata<T>(function.Metadata);

        // Assert the function result
        FunctionResult functionResult = await function.InvokeAsync(new(), new() { ["query"] = "Mock Query" });

        var result = functionResult.GetValue<List<T>>()!;
        Assert.AreEqual(1, result.Count);
        Assert.AreEqual(expectedResult, result[0]);
    }

    internal static void AssertSearchFunctionMetadata<T>(KernelFunctionMetadata metadata)
    {
        // Assert input parameter schema
        Assert.AreEqual(3, metadata.Parameters.Count);
        Assert.AreEqual("{\"description\":\"What to search for\",\"type\":\"string\"}", metadata.Parameters[0].Schema!.ToString());
        Assert.AreEqual("{\"description\":\"Number of results (default value: 2)\",\"type\":\"integer\"}", metadata.Parameters[1].Schema!.ToString());
        Assert.AreEqual("{\"description\":\"Number of results to skip (default value: 0)\",\"type\":\"integer\"}", metadata.Parameters[2].Schema!.ToString());

        // Assert return type schema
        var type = typeof(T).Name;
        var expectedSchema = type switch
        {
            "String" => """{"type":"object","properties":{"TotalCount":{"type":["integer","null"],"default":null},"Metadata":{"type":["object","null"],"default":null},"Results":{"type":"array","items":{"type":"string"}}},"required":["Results"]}""",
            "TextSearchResult" => """{"type":"object","properties":{"TotalCount":{"type":["integer","null"],"default":null},"Metadata":{"type":["object","null"],"default":null},"Results":{"type":"array","items":{"type":"object","properties":{"Name":{"type":["string","null"]},"Link":{"type":["string","null"]},"Value":{"type":"string"}},"required":["Value"]}}},"required":["Results"]}""",
            _ => """{"type":"object","properties":{"TotalCount":{"type":["integer","null"],"default":null},"Metadata":{"type":["object","null"],"default":null},"Results":{"type":"array","items":{"type":"object","properties":{"Name":{"type":["string","null"]},"Link":{"type":["string","null"]},"Value":{"type":"string"}},"required":["Value"]}}},"required":["Results"]}"""
        };
        Assert.AreEqual(expectedSchema, metadata.ReturnParameter.Schema!.ToString());
    }
    #endregion
}
