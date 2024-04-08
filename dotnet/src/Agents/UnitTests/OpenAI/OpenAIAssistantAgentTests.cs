// Copyright (c) Microsoft. All rights reserved.
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI;

/// <summary>
/// Unit testing of <see cref="OpenAIAssistantAgent"/>.
/// </summary>
public class OpenAIAssistantAgentTests
{
    /// <summary>
    /// Verify the invocation and response of <see cref="OpenAIAssistantAgent"/>.
    /// </summary>
    [Fact]
    public void VerifyOpenAIAssistantAgentDefinition()
    {
        //OpenAIAssistantAgent agent =
        //    new(CreateEmptyKernel(), description: "test description", name: "test name")
        //    {
        //        Instructions = "test instructions",
        //    };

        //Assert.NotNull(agent.Id);
        //Assert.Equal("test instructions", agent.Instructions);
        //Assert.Equal("test description", agent.Description);
        //Assert.Equal("test name", agent.Name);
    }

    /// <summary>
    /// Verify the invocation and response of <see cref="OpenAIAssistantAgent"/>.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentInvocationAsync()
    {
        //var agent = new OpenAIAssistantAgent(this.CreateEmptyKernel(), "fake-instructions");

        //var result = await agent.InvokeAsync().ToArrayAsync();

        //mockService.Verify(
        //    x =>
        //        x.GetChatMessageContentsAsync(
        //            It.IsAny<ChatHistory>(),
        //            It.IsAny<PromptExecutionSettings>(),
        //            It.IsAny<Kernel>(),
        //            It.IsAny<CancellationToken>()),
        //    Times.Once);
    }

    private static Kernel CreateEmptyKernel()
    {
        return Kernel.CreateBuilder().Build();
    }
}
