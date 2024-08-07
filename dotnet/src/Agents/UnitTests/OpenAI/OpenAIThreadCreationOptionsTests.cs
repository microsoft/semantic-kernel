// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
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
        OpenAIThreadCreationOptions options = new();

        Assert.Null(options.Messages);
        Assert.Null(options.Metadata);
        Assert.Null(options.VectorStoreId);
        Assert.Null(options.CodeInterpreterFileIds);

        ValidateSerialization(options);
    }

    /// <summary>
    /// Verify initialization.
    /// </summary>
    [Fact]
    public void OpenAIThreadCreationOptionsAssignment()
    {
        OpenAIThreadCreationOptions options =
            new()
            {
                Messages = [new ChatMessageContent(AuthorRole.User, "test")],
                VectorStoreId = "#vs",
                Metadata = new Dictionary<string, string>() { { "a", "1" } },
                CodeInterpreterFileIds = ["file1"],
            };

        Assert.Single(options.Messages);
        Assert.Single(options.Metadata);
        Assert.Equal("#vs", options.VectorStoreId);
        Assert.Single(options.CodeInterpreterFileIds);

        ValidateSerialization(options);
    }

    private static void ValidateSerialization(OpenAIThreadCreationOptions source)
    {
        string json = JsonSerializer.Serialize(source);

        OpenAIThreadCreationOptions? target = JsonSerializer.Deserialize<OpenAIThreadCreationOptions>(json);

        Assert.NotNull(target);
        Assert.Equal(source.VectorStoreId, target.VectorStoreId);
        AssertCollection.Equal(source.CodeInterpreterFileIds, target.CodeInterpreterFileIds);
        AssertCollection.Equal(source.Messages, target.Messages, m => m.Items.Count); // ChatMessageContent already validated for deep serialization
        AssertCollection.Equal(source.Metadata, target.Metadata);
    }
}
