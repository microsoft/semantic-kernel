// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public class KernelFunctionLogMessagesTests
{
    [Theory]
    [InlineData(typeof(string))]
    [InlineData(typeof(int))]
    [InlineData(typeof(bool))]
    [InlineData(typeof(ChatMessageContent))]
    [InlineData(typeof(User))]
    public void ItShouldLogFunctionResultOfAnyType(Type resultType)
    {
        // Arrange
        (object FunctionResult, string LogMessage) testData = resultType switch
        {
            Type t when t == typeof(string) => ("test-string", "Function p1-f1 result: test-string"),
            Type t when t == typeof(int) => (6, "Function p1-f1 result: 6"),
            Type t when t == typeof(bool) => (true, "Function p1-f1 result: true"),
            Type t when t == typeof(ChatMessageContent) => (new ChatMessageContent(AuthorRole.Assistant, "test-content"), "Function p1-f1 result: test-content"),
            Type t when t == typeof(User) => (new User { Name = "test-user-name" }, "Function p1-f1 result: {\"name\":\"test-user-name\"}"),
            _ => throw new ArgumentException("Invalid type")
        };

        var logger = new Mock<ILogger>();
        logger.Setup(l => l.IsEnabled(It.IsAny<LogLevel>())).Returns(true);

        var functionResult = new FunctionResult(KernelFunctionFactory.CreateFromMethod(() => { }), testData.FunctionResult);

        // Act
        logger.Object.LogFunctionResultValue("p1", "f1", functionResult);

        // Assert
        logger.Verify(l => l.Log(
            LogLevel.Trace,
            0,
            It.Is<It.IsAnyType>((o, _) => o.ToString() == testData.LogMessage),
            null,
            It.IsAny<Func<It.IsAnyType, Exception?, string>>()));
    }

    [Fact]
    public void ItShouldFallBackToToStringWhenJsonSerializationIsNotSupported()
    {
        // Arrange
        var logger = new Mock<ILogger>();
        logger.Setup(l => l.IsEnabled(It.IsAny<LogLevel>())).Returns(true);

        // TypeNotInJsonContext cannot be cast to string and is not registered in the restricted JSON context
        var unserializableValue = new TypeNotInJsonContext();
        var functionResult = new FunctionResult(KernelFunctionFactory.CreateFromMethod(() => { }), unserializableValue);

        // Use a restricted JsonSerializerOptions that knows about object but not TypeNotInJsonContext,
        // simulating the AOT scenario where AbstractionsJsonContext is used and an unregistered
        // MEAI type (e.g. Microsoft.Extensions.AI.TextContent) is returned from an MCP tool.
        var restrictedOptions = RestrictedJsonContext.Default.Options;

        // Act
        logger.Object.LogFunctionResultValue("p1", "f1", functionResult, restrictedOptions);

        // Assert - ToString() fallback should have been used, not the error message
        logger.Verify(l => l.Log(
            LogLevel.Trace,
            0,
            It.Is<It.IsAnyType>((o, _) => o.ToString() == "Function p1-f1 result: TypeNotInJsonContext()"),
            null,
            It.IsAny<Func<It.IsAnyType, Exception?, string>>()));
    }

    private sealed class User
    {
        [JsonPropertyName("name")]
        public string? Name { get; set; }
    }

    private sealed class TypeNotInJsonContext
    {
        public override string ToString() => "TypeNotInJsonContext()";
    }

    [JsonSerializable(typeof(IDictionary<string, object?>))]
    [JsonSerializable(typeof(object))]
    private sealed partial class RestrictedJsonContext : JsonSerializerContext { }
}
