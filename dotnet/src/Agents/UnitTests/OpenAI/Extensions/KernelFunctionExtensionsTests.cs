// Copyright (c) Microsoft. All rights reserved.
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.OpenAI.Extensions;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI.Extensions;

/// <summary>
/// Unit testing of <see cref="KernelFunctionExtensions"/>.
/// </summary>
public class KernelFunctionExtensionsTests
{
    /// <summary>
    /// $$$
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
    /// $$$
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentInvocationAsync()
    {
        await Task.Yield();
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
}
