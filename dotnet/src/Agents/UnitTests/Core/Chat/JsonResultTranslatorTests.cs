// Copyright (c) Microsoft. All rights reserved.
using System.Text.Json;
using Microsoft.SemanticKernel.Agents.Chat;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Core.Chat;

/// <summary>
/// Unit testing of <see cref="JsonResultTranslator"/>.
/// </summary>
public class JsonResultTranslatorTests
{
    /// <summary>
    /// Verify processing result for object result.
    /// </summary>
    [Theory]
    [InlineData(JsonObject)]
    [InlineData(JsonObjectDelimited)]
    [InlineData(JsonObjectDelimitedWithPrefix)]
    [InlineData(JsonObjectDelimiteDegenerate)]
    public void VerifyJsonResultTranslatorObjects(string input)
    {
        TestResult? result = JsonResultTranslator.Translate<TestResult>(input);
        Assert.NotNull(result);
        Assert.Equal("Hi!", result?.message);
    }

    /// <summary>
    /// Verify processing result for object result.
    /// </summary>
    [Fact]
    public void VerifyJsonResultTranslatorBad()
    {
        Assert.Throws<JsonException>(() => JsonResultTranslator.Translate<TestResult>(NotJson));
    }

    /// <summary>
    /// Verify processing result for object result.
    /// </summary>
    [Fact]
    public void VerifyJsonResultTranslatorString()
    {
        string? result = JsonResultTranslator.Translate<string>(JsonString);
        Assert.NotNull(result);
        Assert.Equal("Hi!", result);
    }

    private record struct TestResult(string message);

    private const string NotJson =
        """
        Hi!
        """;

    private const string JsonString =
        """
        "Hi!"
        """;

    private const string JsonObject =
        """
        {
            "message": "Hi!"
        }
        """;

    private const string JsonObjectDelimited =
        $$$"""
        ```
        {{{JsonObject}}}```
        """;

    private const string JsonObjectDelimitedWithPrefix =
        $$$"""
        ```json
        {{{JsonObject}}}
        ```
        """;

    private const string JsonObjectDelimiteDegenerate =
        $$$"""
        ```
        {{{JsonObject}}}
        """;
}
