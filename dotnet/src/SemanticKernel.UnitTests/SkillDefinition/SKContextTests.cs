// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.SkillDefinition;

public class SKContextTests
{
    private readonly Mock<ISkillCollection> _skills = new();

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
    public async Task ItHasHelpersForSkillCollectionAsync()
    {
        // Arrange
        IDictionary<string, ISKFunction> skill = KernelBuilder.Create().ImportSkill(new Parrot(), "test");
        this._skills.Setup(x => x.GetFunction("func")).Returns(skill["say"]);
        var (kernel, kernelContext) = this.SetupKernelMock(this._skills.Object);

        var target = new SKContext(kernelContext.Object, new ContextVariables());
        Assert.NotNull(target.Skills);

        // Act
        var say = target.Skills.GetFunction("func");
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
