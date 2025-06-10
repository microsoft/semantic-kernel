// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.CopilotStudio.Internal;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.CopilotStudio;

public class ContentProcessorTests
{
    [Fact]
    public void ConvertToStreaming_EmptyCollection_ReturnsEmptyEnumerable()
    {
        // Arrange
        ChatMessageContentItemCollection collection = [];

        // Act
        IEnumerable<StreamingKernelContent> result = ContentProcessor.ConvertToStreaming(collection, NullLogger.Instance);

        // Assert
        Assert.Empty(result);
    }

    [Fact]
    public void ConvertToStreaming_TextContent_ReturnsStreamingTextContent()
    {
        // Arrange
        ChatMessageContentItemCollection collection = [];
        TextContent textContent = new("Display text");
        collection.Add(textContent);

        // Act
        IEnumerable<StreamingKernelContent> result = ContentProcessor.ConvertToStreaming(collection, NullLogger.Instance);

        // Assert
        StreamingKernelContent streamingContent = Assert.Single(result);
        Assert.IsType<StreamingTextContent>(streamingContent);
    }

    [Fact]
    public void ConvertToStreaming_ReasoningContent_ReturnsStreamingReasoningContent()
    {
        // Arrange
        ChatMessageContentItemCollection collection = [];
        ReasoningContent reasoningContent = new("Reasoning text");
        collection.Add(reasoningContent);

        // Act
        IEnumerable<StreamingKernelContent> result = ContentProcessor.ConvertToStreaming(collection, NullLogger.Instance);

        // Assert
        StreamingKernelContent streamingContent = Assert.Single(result);
        Assert.IsType<StreamingReasoningContent>(streamingContent);
    }

    [Fact]
    public void ConvertToStreaming_ActionContent_ReturnsStreamingActionContent()
    {
        // Arrange
        ChatMessageContentItemCollection collection = [];
        ActionContent actionContent = new("Action text");
        collection.Add(actionContent);

        // Act
        IEnumerable<StreamingKernelContent> result = ContentProcessor.ConvertToStreaming(collection, NullLogger.Instance);

        // Assert
        StreamingKernelContent streamingContent = Assert.Single(result);
        Assert.IsType<StreamingActionContent>(streamingContent);
    }

    [Fact]
    public void ConvertToStreaming_MixedContentTypes_ReturnsCorrespondingStreamingTypes()
    {
        // Arrange
        ChatMessageContentItemCollection collection = [];
        TextContent textContent = new("Text content");
        ReasoningContent reasoningContent = new("Reasoning content");
        ActionContent actionContent = new("Action content");
        collection.Add(textContent);
        collection.Add(reasoningContent);
        collection.Add(actionContent);

        // Act
        List<StreamingKernelContent> result = [.. ContentProcessor.ConvertToStreaming(collection, NullLogger.Instance)];

        // Assert
        Assert.Equal(3, result.Count);
        Assert.IsType<StreamingTextContent>(result[0]);
        Assert.IsType<StreamingReasoningContent>(result[1]);
        Assert.IsType<StreamingActionContent>(result[2]);
    }

    [Fact]
    public void ConvertToStreaming_UnknownContentType_LogsWarningAndSkipsContent()
    {
        // Arrange
        ChatMessageContentItemCollection collection = [];
        KernelContent unknownContent = new TestUnknownContent();
        collection.Add(unknownContent);

        // Create test logger to capture logs
        TestLogger testLogger = new();

        // Act
        IEnumerable<StreamingKernelContent> result = ContentProcessor.ConvertToStreaming(collection, testLogger);

        // Assert
        Assert.Empty(result);
        Assert.Single(testLogger.LoggedWarnings);
        Assert.Contains("Unknown content type 'TestUnknownContent' received.", testLogger.LoggedWarnings[0]);
    }

    // Test helper classes
    private sealed class TestUnknownContent : KernelContent;

    private sealed class TestLogger : ILogger
    {
        public List<string> LoggedWarnings { get; } = [];

        public bool IsEnabled(LogLevel logLevel) => true;

        public void Log<TState>(LogLevel logLevel, EventId eventId, TState state, Exception? exception, Func<TState, Exception?, string> formatter)
        {
            if (logLevel == LogLevel.Warning)
            {
                this.LoggedWarnings.Add(formatter(state, exception));
            }
        }

        IDisposable? ILogger.BeginScope<TState>(TState state) => null;
    }
}
