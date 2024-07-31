// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
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
    }

    /// <summary>
    /// Verify initialization.
    /// </summary>
    [Fact]
    public void OpenAIThreadCreationOptionsAssignment()
    {
        OpenAIThreadCreationOptions definition =
            new()
            {
                Messages = [new ChatMessageContent(AuthorRole.User, "test")],
                VectorStoreId = "#vs",
                Metadata = new Dictionary<string, string>() { { "a", "1" } },
                CodeInterpreterFileIds = ["file1"],
            };

        Assert.Single(definition.Messages);
        Assert.Single(definition.Metadata);
        Assert.Equal("#vs", definition.VectorStoreId);
        Assert.Single(definition.CodeInterpreterFileIds);
    }
}
