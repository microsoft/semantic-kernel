// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI;

/// <summary>
/// Unit testing of <see cref="OpenAIThreadCreationSettings"/>.
/// </summary>
public class OpenAIThreadCreationSettingsTests
{
    /// <summary>
    /// Verify initial state.
    /// </summary>
    [Fact]
    public void OpenAIThreadCreationSettingsInitialState()
    {
        OpenAIThreadCreationSettings settings = new();

        Assert.Null(settings.Messages);
        Assert.Null(settings.Metadata);
        Assert.Null(settings.VectorStoreId);
        Assert.Null(settings.CodeInterpterFileIds);
        Assert.False(settings.EnableCodeInterpreter);
    }

    /// <summary>
    /// Verify initialization.
    /// </summary>
    [Fact]
    public void OpenAIThreadCreationSettingsAssignment()
    {
        OpenAIThreadCreationSettings definition =
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
