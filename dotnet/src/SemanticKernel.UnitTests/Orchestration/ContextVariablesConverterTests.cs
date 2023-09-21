// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using Microsoft.SemanticKernel.Orchestration;
using Xunit;

namespace SemanticKernel.UnitTests.Orchestration;

/// <summary>
/// Unit tests of <see cref="ContextVariablesConverter"/>.
/// </summary>
public class ContextVariablesConverterTests
{
    [Fact]
    public void ReadFromJsonSucceeds()
    {
        // Arrange
        string json = /*lang=json,strict*/ @"[{""Key"":""a"", ""Value"":""b""}]";
        var options = new JsonSerializerOptions();
        options.Converters.Add(new ContextVariablesConverter());

        // Act
        var result = JsonSerializer.Deserialize<ContextVariables>(json, options);

        // Assert
        Assert.Equal("b", result!["a"]);
        Assert.Throws<KeyNotFoundException>(() => result!["INPUT"]);
        Assert.Equal(string.Empty, result!.Input);
    }

    [Fact]
    public void ReadFromJsonWrongTypeThrows()
    {
        // Arrange
        string json = /*lang=json,strict*/ @"[{""Key"":""a"", ""Value"":""b""}]";
        var options = new JsonSerializerOptions();
        options.Converters.Add(new ContextVariablesConverter());

        // Act and Assert
        Assert.Throws<JsonException>(() => JsonSerializer.Deserialize<Dictionary<string, string>>(json, options));
    }

    [Fact]
    public void ReadFromJsonSucceedsWithInput()
    {
        // Arrange
        string json = /*lang=json,strict*/ @"[{""Key"":""INPUT"", ""Value"":""c""}, {""Key"":""a"", ""Value"":""b""}]";
        var options = new JsonSerializerOptions();
        options.Converters.Add(new ContextVariablesConverter());

        // Act
        var result = JsonSerializer.Deserialize<ContextVariables>(json, options);

        // Assert
        Assert.Equal("b", result!["a"]);
        Assert.Equal("c", result!["INPUT"]);
    }

    // input value
    // params key/value
    [Theory]
    [InlineData("", new[] { "a", "b" }, new[]
    {
        /*lang=json,strict*/ @"{""Key"":""INPUT"",""Value"":""""}", /*lang=json,strict*/ @"{""Key"":""a"",""Value"":""b""}"
    })]
    [InlineData("c", new[] { "a", "b" }, new[]
    {
        /*lang=json,strict*/ @"{""Key"":""INPUT"",""Value"":""c""}", /*lang=json,strict*/ @"{""Key"":""a"",""Value"":""b""}"
    })]
    [InlineData("c", new[] { "a", "b", "d", "e" }, new[]
    {
        /*lang=json,strict*/ @"{""Key"":""INPUT"",""Value"":""c""}", /*lang=json,strict*/ @"{""Key"":""a"",""Value"":""b""}", /*lang=json,strict*/
        @"{""Key"":""d"",""Value"":""e""}"
    })]
    public void WriteToJsonSucceeds(string inputValue, IList<string> contextToSet, IList<string> expectedJson)
    {
        // Arrange
        var options = new JsonSerializerOptions();
        options.Converters.Add(new ContextVariablesConverter());
        var context = new ContextVariables();
        if (inputValue != null)
        {
            context.Update(inputValue);
        }

        for (int i = 0; i < contextToSet.Count; i += 2)
        {
            context.Set(contextToSet[i], contextToSet[i + 1]);
        }

        // Act
        string result = JsonSerializer.Serialize(context, options);

        // Assert
        foreach (string key in expectedJson)
        {
            Assert.Contains(key, result, StringComparison.Ordinal);
        }
    }

    [Fact]
    public void WriteToJsonSucceedsAfterClearing()
    {
        // Arrange
        var options = new JsonSerializerOptions();
        options.Converters.Add(new ContextVariablesConverter());
        var context = new ContextVariables();
        context.Set("a", "b");
        context.Set("INPUT", "c");
        context.Set("d", "e");
        context.Set("f", "ThingToBeCleared");
        context.Set("f", null);
        context.Set("g", string.Empty);

        // Act
        string result = JsonSerializer.Serialize(context, options);

        // Assert
        Assert.Contains( /*lang=json,strict*/ @"{""Key"":""INPUT"",""Value"":""c""}", result, StringComparison.Ordinal);
        Assert.Contains( /*lang=json,strict*/ @"{""Key"":""a"",""Value"":""b""}", result, StringComparison.Ordinal);
        Assert.Contains( /*lang=json,strict*/ @"{""Key"":""d"",""Value"":""e""}", result, StringComparison.Ordinal);
        Assert.DoesNotContain(@"""Key"":""f""", result, StringComparison.Ordinal);
        Assert.Contains( /*lang=json,strict*/ @"{""Key"":""g"",""Value"":""""}", result, StringComparison.Ordinal);
    }

    // Error Tests
    [Fact]
    public void ReadFromJsonReturnsNullWithNull()
    {
        // Arrange
        string json = /*lang=json,strict*/ "null";
        var options = new JsonSerializerOptions();
        options.Converters.Add(new ContextVariablesConverter());

        // Act
        var result = JsonSerializer.Deserialize<ContextVariables>(json, options);

        // Assert
        Assert.Null(result);
    }

    [Fact]
    public void ReadFromJsonReturnsDefaultWithEmpty()
    {
        // Arrange
        string json = /*lang=json,strict*/ "[]";
        var options = new JsonSerializerOptions();
        options.Converters.Add(new ContextVariablesConverter());

        // Act
        var result = JsonSerializer.Deserialize<ContextVariables>(json, options);

        // Assert
        Assert.NotNull(result);
        Assert.Throws<KeyNotFoundException>(() => result!["INPUT"]);
        Assert.Equal(string.Empty, result!.Input);
    }

    [Fact]
    public void ReadFromJsonThrowsWithInvalidJson()
    {
        // Arrange
#pragma warning disable JSON001 // Invalid JSON pattern
        string json = /*lang=json,strict*/ @"[{""Key"":""a"", ""Value"":""b""";
#pragma warning restore JSON001 // Invalid JSON pattern
        var options = new JsonSerializerOptions();
        options.Converters.Add(new ContextVariablesConverter());

        // Act & Assert
        Assert.Throws<JsonException>(() => JsonSerializer.Deserialize<ContextVariables>(json, options));
    }

    [Fact]
    public void ReadFromJsonThrowsWithInvalidJson2()
    {
        // Arrange
        string json = /*lang=json,strict*/ @"[{""Keys"":""a"", ""Value"":""b""}]";
        var options = new JsonSerializerOptions();
        options.Converters.Add(new ContextVariablesConverter());

        // Act & Assert
        Assert.Throws<JsonException>(() => JsonSerializer.Deserialize<ContextVariables>(json, options));
    }
}
