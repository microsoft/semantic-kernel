// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;
using Xunit;

namespace Microsoft.SemanticKernel.Process.UnitTests.Workflows;

/// <summary>
/// Base for directly testing AnswerQuestionWithAI.
/// </summary>
public sealed class AnswerQuestionWithAIActionTest
{
    [Fact]
    public Task EmptyTestAsync()
    {
        AnswerQuestionWithAI action = new();
        // %%% TODO: Something
        return Task.CompletedTask;
    }
}
