// Copyright (c) Microsoft. All rights reserved.
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.Chat;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Core.Chat;

/// <summary>
/// Unit testing of <see cref="RegexTerminationStrategy"/>.
/// </summary>
public partial class RegexTerminationStrategyTests
{
    /// <summary>
    /// Verify abililty of strategy to match expression.
    /// </summary>
    [Fact]
    public async Task VerifyExpressionTerminationStrategyAsync()
    {
        // Arrange
        RegexTerminationStrategy strategy = new("test");

        Regex r = MyRegex();

        // Act and Assert
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
        // Arrange
        ChatMessageContent message = new(AuthorRole.Assistant, content);
        MockAgent agent = new();

        // Act
        var result = await strategyRoot.ShouldTerminateAsync(agent, [message]);

        // Assert
        Assert.Equal(expectedResult, result);
    }

    [GeneratedRegex("(?:^|\\W)test(?:$|\\W)")]
    private static partial Regex MyRegex();
}
