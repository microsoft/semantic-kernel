// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Core;

/// <summary>
/// Unit testing of <see cref="ChatCompletionAgent"/>.
/// </summary>
public class ChatCompletionAgentTests
{
    /// <summary>
    /// $$$
    /// </summary>
    [Fact]
    public void VerifySomething()
    {
        //Mock<IChatCompletionService> $$$
        ChatCompletionAgent agent = new(Kernel.CreateBuilder().Build());
    }
}
