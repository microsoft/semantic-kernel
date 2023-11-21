// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Experimental.Assistants.Extensions;
using Xunit;

namespace SemanticKernel.Experimental.Assistants.UnitTests.Extensions;

[Trait("Category", "Unit Tests")]
[Trait("Feature", "Assistant")]
public sealed class KernelExtensionTests
{
    private const string TwoPartToolName = "Fake-Bogus";

    [Fact]
    public static void InvokeTwoPartTool()
    {
        //Arrange
        var function = SKFunctionFactory.CreateFromMethod(() => { }, functionName: "Bogus");

        var kernel = KernelBuilder.Create();
        kernel.Plugins.Add(new SKPlugin("Fake", new[] { function }));

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
        var kernel = KernelBuilder.Create();

        //Act & Assert
        Assert.Throws<SKException>(() => kernel.GetAssistantTool(toolName));
    }
}
