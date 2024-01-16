// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Experimental.Agents.Exceptions;
using Microsoft.SemanticKernel.Experimental.Agents.Extensions;
using Xunit;

namespace SemanticKernel.Experimental.Agents.UnitTests;

[Trait("Category", "Unit Tests")]
[Trait("Feature", "Agent")]
public sealed class KernelExtensionTests
{
    private const string TwoPartToolName = "Fake-Bogus";

    [Fact]
    public static void InvokeTwoPartTool()
    {
        //Arrange
        var function = KernelFunctionFactory.CreateFromMethod(() => { }, functionName: "Bogus");

        var kernel = new Kernel();
        kernel.ImportPluginFromFunctions("Fake", new[] { function });

        //Act
        var tool = kernel.GetAssistantTool(TwoPartToolName);

        //Assert
        Assert.NotNull(tool);
        Assert.Equal("Bogus", tool.Name);
    }

    [Theory]
    [InlineData("Bogus")]
    [InlineData("i-am-not-valid")]
    public static void InvokeInvalidSinglePartTool(string toolName)
    {
        //Arrange
        var kernel = new Kernel();

        //Act & Assert
        Assert.Throws<AgentException>(() => kernel.GetAssistantTool(toolName));
    }
}
