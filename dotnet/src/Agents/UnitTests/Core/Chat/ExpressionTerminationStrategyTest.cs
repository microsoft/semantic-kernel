// Copyright (c) Microsoft. All rights reserved.
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Chat;
using Microsoft.SemanticKernel.ChatCompletion;
using Moq;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Core.Chat;

/// <summary>
/// Unit testing of <see cref="ExpressionTerminationStrategy"/>.
/// </summary>
public class ExpressionTerminationStrategyTest
{
    /// <summary>
    /// $$$
    /// </summary>
    [Fact]
    public async Task VerifyExpressionTerminationStrategyAsync()
    {
        ExpressionTerminationStrategy strategy = new("test");

        await VerifyResultAsync(
            expectedResult: false,
            new("(?:^|\\W)test(?:$|\\W)"),
            content: "fred");

        await VerifyResultAsync(
            expectedResult: true,
            new("(?:^|\\W)test(?:$|\\W)"),
            content: "this is a test");
    }

    private static async Task VerifyResultAsync(bool expectedResult, ExpressionTerminationStrategy strategyRoot, string content)
    {
        ChatMessageContent message = new(AuthorRole.Assistant, content);
        Mock<Agent> agent = new();
        var result = await strategyRoot.ShouldTerminateAsync(agent.Object, new[] { message });
        Assert.Equal(expectedResult, result);
    }
}
