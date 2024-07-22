// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI;

/// <summary>
/// Unit testing of <see cref="RunPollingOptions"/>.
/// </summary>
public class RunPollingOptionsTests
{
    /// <summary>
    /// Verify initial state.
    /// </summary>
    [Fact]
    public void RunPollingOptionsInitialState()
    {
        OpenAIThreadCreationOptions options = new();

        Assert.Null(options.Messages);
        Assert.Null(options.Metadata);
        Assert.Null(options.VectorStoreId);
        Assert.Null(options.CodeInterpterFileIds);
        Assert.False(options.EnableCodeInterpreter);
    }

    /// <summary>s
    /// Verify initialization.
    /// </summary>
    [Fact]
    public void RunPollingOptionsAssignment()
    {
        OpenAIThreadCreationOptions definition =
            new()
            {
                Messages = [new ChatMessageContent(AuthorRole.User, "test")],
                VectorStoreId = "#vs",
                Metadata = new Dictionary<string, string>() { { "a", "1" } },
                CodeInterpterFileIds = ["file1"],
                EnableCodeInterpreter = true,
            };

        Assert.Single(definition.Messages);
        Assert.Single(definition.Metadata);
        Assert.Equal("#vs", definition.VectorStoreId);
        Assert.Single(definition.CodeInterpterFileIds);
        Assert.True(definition.EnableCodeInterpreter);
    }
}
