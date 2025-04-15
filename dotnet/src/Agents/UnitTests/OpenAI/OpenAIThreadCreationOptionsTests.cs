// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using SemanticKernel.Agents.UnitTests.Test;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI;

/// <summary>
/// Unit testing of <see cref="OpenAIThreadCreationOptions"/>.
/// </summary>
public class OpenAIThreadCreationOptionsTests
{
    /// <summary>
    /// Verify initial state.
    /// </summary>
    [Fact]
    public void OpenAIThreadCreationOptionsInitialState()
    {
        // Arrange
        OpenAIThreadCreationOptions options = new();

        // Assert
        Assert.Null(options.Messages);
        Assert.Null(options.Metadata);
        Assert.Null(options.VectorStoreId);
        Assert.Null(options.CodeInterpreterFileIds);

        // Act and Assert
        ValidateSerialization(options);
    }

    /// <summary>
    /// Verify initialization.
    /// </summary>
    [Fact]
    public void OpenAIThreadCreationOptionsAssignment()
    {
        // Arrange
        OpenAIThreadCreationOptions options =
            new()
            {
                Messages = [new ChatMessageContent(AuthorRole.User, "test")],
                VectorStoreId = "#vs",
                Metadata = new Dictionary<string, string>() { { "a", "1" } },
                CodeInterpreterFileIds = ["file1"],
            };

        // Assert
        Assert.Single(options.Messages);
        Assert.Single(options.Metadata);
        Assert.Equal("#vs", options.VectorStoreId);
        Assert.Single(options.CodeInterpreterFileIds);

        // Act and Assert
        ValidateSerialization(options);
    }

    private static void ValidateSerialization(OpenAIThreadCreationOptions source)
    {
        // Act
        string json = JsonSerializer.Serialize(source);

        OpenAIThreadCreationOptions? target = JsonSerializer.Deserialize<OpenAIThreadCreationOptions>(json);

        // Assert
        Assert.NotNull(target);
        Assert.Equal(source.VectorStoreId, target.VectorStoreId);
        AssertCollection.Equal(source.CodeInterpreterFileIds, target.CodeInterpreterFileIds);
        AssertCollection.Equal(source.Messages, target.Messages, m => m.Items.Count); // ChatMessageContent already validated for deep serialization
        AssertCollection.Equal(source.Metadata, target.Metadata);
    }
}
