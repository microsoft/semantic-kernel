// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public class SKContextTests
{
    private readonly Mock<IReadOnlyFunctionCollection> _functions = new();
    private readonly Mock<IKernel> _kernel;

    [Fact]
    public void ItHasHelpersForContextVariables()
    {
        // Arrange
        var variables = new ContextVariables();
        var target = new SKContext(new Mock<IKernelExecutionContext>().Object, variables);
        variables.Set("foo1", "bar1");

        // Act
        target.Variables["foo2"] = "bar2";
        target.Variables["INPUT"] = Guid.NewGuid().ToString("N");

        // Assert
        Assert.Equal("bar1", target.Variables["foo1"]);
        Assert.Equal("bar1", target.Variables["foo1"]);
        Assert.Equal("bar2", target.Variables["foo2"]);
        Assert.Equal("bar2", target.Variables["foo2"]);
        Assert.Equal(target.Variables["INPUT"], target.Result);
        Assert.Equal(target.Variables["INPUT"], target.ToString());
        Assert.Equal(target.Variables["INPUT"], target.Variables.Input);
        Assert.Equal(target.Variables["INPUT"], target.Variables.ToString());
    }

    [Fact]
    public async Task ItHasHelpersForFunctionCollectionAsync()
    {
        // Arrange
        IDictionary<string, ISKFunction> plugin = KernelBuilder.Create().ImportPlugin(new Parrot(), "test");
        this._functions.Setup(x => x.GetFunction("func")).Returns(plugin["say"]);
        var (kernel, kernelContext) = this.SetupKernelMock(this._functions.Object);

        var target = new SKContext(kernelContext.Object, new ContextVariables());
        Assert.NotNull(target.Functions);

        // Act
        var say = target.Functions.GetFunction("func");
        SKContext result = await say.InvokeAsync("ciao", kernel.Object);

        // Assert
        Assert.Equal("ciao", result.Result);
    }

    private (Mock<IKernel> kernelMock, Mock<IKernelExecutionContext> kernelContextMock) SetupKernelMock(ISkillCollection? skills = null)
    {
        skills ??= new Mock<ISkillCollection>().Object;

        var kernel = new Mock<IKernel>();
        var kernelContext = new Mock<IKernelExecutionContext>();

        kernel.SetupGet(x => x.Skills).Returns(skills);
        kernelContext.SetupGet(x => x.Skills).Returns(skills);
        kernel.SetupGet(x => x.Skills).Returns(skills);
        kernel.Setup(k => k.CreateNewContext(It.IsAny<ContextVariables>(), It.IsAny<IReadOnlySkillCollection>())).Returns<ContextVariables, IReadOnlySkillCollection>((contextVariables, skills) =>
        {
            kernelContext.SetupGet(x => x.Skills).Returns(skills ?? kernel.Object.Skills);
            return new SKContext(kernelContext.Object, contextVariables);
        });

        kernelContext.Setup(k => k.CreateNewContext(It.IsAny<ContextVariables>(), It.IsAny<IReadOnlySkillCollection>())).Returns<ContextVariables, IReadOnlySkillCollection>((contextVariables, skills) =>
        {
            kernelContext.SetupGet(x => x.Skills).Returns(skills ?? kernel.Object.Skills);
            return new SKContext(kernelContext.Object, contextVariables);
        });

        return (kernel, kernelContext);
    }

    private sealed class Parrot
    {
        [SKFunction, Description("say something")]
        // ReSharper disable once UnusedMember.Local
        public string Say(string input)
        {
            return input;
        }
    }
}
