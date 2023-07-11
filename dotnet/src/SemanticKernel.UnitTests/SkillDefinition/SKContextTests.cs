// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.SkillDefinition;

public class SKContextTests
{
    private readonly Mock<IReadOnlySkillCollection> _skills;
    private readonly Mock<ILogger> _log;

    public SKContextTests()
    {
        this._skills = new Mock<IReadOnlySkillCollection>();
        this._log = new Mock<ILogger>();
    }

    [Fact]
    public void ItHasHelpersForContextVariables()
    {
        // Arrange
        var variables = new ContextVariables();
        var target = new SKContext(variables, skills: this._skills.Object, logger: this._log.Object);
        variables.Set("foo1", "bar1");

        // Act
        target["foo2"] = "bar2";
        target["INPUT"] = Guid.NewGuid().ToString("N");

        // Assert
        Assert.Equal("bar1", target["foo1"]);
        Assert.Equal("bar1", target.Variables["foo1"]);
        Assert.Equal("bar2", target["foo2"]);
        Assert.Equal("bar2", target.Variables["foo2"]);
        Assert.Equal(target["INPUT"], target.Result);
        Assert.Equal(target["INPUT"], target.ToString());
        Assert.Equal(target["INPUT"], target.Variables.Input);
        Assert.Equal(target["INPUT"], target.Variables.ToString());
    }

    [Fact]
    public async Task ItHasHelpersForSkillCollectionAsync()
    {
        // Arrange
        IDictionary<string, ISKFunction> skill = KernelBuilder.Create().ImportSkill(new Parrot(), "test");
        this._skills.Setup(x => x.GetFunction("func")).Returns(skill["say"]);
        var target = new SKContext(new ContextVariables(), NullMemory.Instance, this._skills.Object, this._log.Object);
        Assert.NotNull(target.Skills);

        // Act
        var say = target.Skills.GetFunction("func");
        SKContext result = await say.InvokeAsync("ciao");

        // Assert
        Assert.Equal("ciao", result.Result);
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
