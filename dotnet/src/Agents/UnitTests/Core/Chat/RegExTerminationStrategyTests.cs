// Copyright (c) Microsoft. All rights reserved.
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Chat;
using Microsoft.SemanticKernel.ChatCompletion;
using Moq;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Core.Chat;

/// <summary>
/// Unit testing of <see cref="RegexTerminationStrategy"/>.
/// </summary>
public class RegexTerminationStrategyTests
{
    /// <summary>
    /// Verify abililty of strategy to match expression.
    /// </summary>
    [Fact]
    public async Task VerifyExpressionTerminationStrategyAsync()
    {
        RegexTerminationStrategy strategy = new("test");

        Regex r = new("(?:^|\\W)test(?:$|\\W)");

        await VerifyResultAsync(
            expectedResult: false,
            new(r),
            content: "fred");

        await VerifyResultAsync(
            expectedResult: true,
            new(r),
            content: "this is a test");
    }

    private static async Task VerifyResultAsync(bool expectedResult, RegexTerminationStrategy strategyRoot, string content)
    {
        ChatMessageContent message = new(AuthorRole.Assistant, content);
        Mock<Agent> agent = new();
        var result = await strategyRoot.ShouldTerminateAsync(agent.Object, [message]);
        Assert.Equal(expectedResult, result);
    }
}
