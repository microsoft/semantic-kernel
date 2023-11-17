// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Experimental.Assistants.Extensions;
using Moq;
using Xunit;

namespace SemanticKernel.Experimental.Assistants.UnitTests.Extensions;

[Trait("Category", "Unit Tests")]
[Trait("Feature", "Assistant")]
public sealed class KernelExtensionTests
{
    private const string SinglePartToolName = "Bogus";
    private const string TwoPartToolName = "Fake-Bogus";

    [Fact]
    public static void InvokeSinglePartTool()
    {
        var mockFunctionCollection = new Mock<IReadOnlyFunctionCollection>();
        var kernel = new Mock<IKernel>();
        kernel.SetupGet(k => k.Functions).Returns(mockFunctionCollection.Object);

        kernel.Object.GetAssistantTool(SinglePartToolName);

        kernel.Verify(x => x.Functions.GetFunction(SinglePartToolName), Times.Once());
        kernel.Verify(x => x.Functions.GetFunction(It.IsAny<string>(), SinglePartToolName), Times.Never());
    }

    [Fact]
    public static void InvokeTwoPartTool()
    {
        var mockFunctionCollection = new Mock<IReadOnlyFunctionCollection>();
        var kernel = new Mock<IKernel>();
        kernel.SetupGet(k => k.Functions).Returns(mockFunctionCollection.Object);

        kernel.Object.GetAssistantTool(TwoPartToolName);

        kernel.Verify(x => x.Functions.GetFunction(SinglePartToolName), Times.Never());
        kernel.Verify(x => x.Functions.GetFunction("Fake", SinglePartToolName), Times.Once());
    }

    [Fact]
    public static void InvokeInvalidThreePartTool()
    {
        var mockFunctionCollection = new Mock<IReadOnlyFunctionCollection>();
        var kernel = new Mock<IKernel>();
        kernel.SetupGet(k => k.Functions).Returns(mockFunctionCollection.Object);

        Assert.Throws<SKException>(() => kernel.Object.GetAssistantTool("i-am-not-valid"));

        kernel.Verify(x => x.Functions.GetFunction(SinglePartToolName), Times.Never());
        kernel.Verify(x => x.Functions.GetFunction("Fake", SinglePartToolName), Times.Never());
    }
}
