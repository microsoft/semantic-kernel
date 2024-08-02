// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.Planning.PowerShell;
using Microsoft.SemanticKernel.SkillDefinition;
using Moq;
using Xunit;

namespace SemanticKernel.Extensions.UnitTests.Planning.PowerShell;

/// <summary>
/// Unit tests for <see cref="PowerShellParser"/>.
/// </summary>
public class PowerShellParserTests
{
    [Fact]
    public void ItParsesScriptCorrectly()
    {
        // Arrange
        const string Script =
            "$poem = Invoke-RestMethod -Uri \"sk://kernel/WriterSkill.ShortPoem\" -Method Post -Body @{input=\"John Doe\"}\n" +
            "$translatedPoem = Invoke-RestMethod -Uri \"sk://kernel/WriterSkill.Translate\" -Method Post -Body @{language=\"Italian\"; input=$poem}\n" +
            "$translatedPoem";

        const string Goal = "Test goal";

        // Act
        var plan = PowerShellParser.ToPlanFromScript(Script, Goal, (skillName, functionName) => this.GetMockFunction(functionName));

        // Assert
        Assert.Equal(Goal, plan.Description);
        Assert.Equal(Script, plan.OriginalPlan);

        Assert.Equal(2, plan.Steps.Count);

        var firstFunction = plan.Steps[0];
        var secondFunction = plan.Steps[1];

        Assert.Equal(firstFunction.Name, "ShortPoem");
        Assert.Equal(firstFunction.SkillName, "WriterSkill");
        Assert.Equal(firstFunction.Parameters["input"], "John Doe");
        Assert.Equal(firstFunction.Outputs[0], "poem");

        Assert.Equal(secondFunction.Name, "Translate");
        Assert.Equal(secondFunction.SkillName, "WriterSkill");
        Assert.Equal(secondFunction.Parameters["input"], "$poem");
        Assert.Equal(secondFunction.Parameters["language"], "Italian");
        Assert.Equal(secondFunction.Outputs[0], "translatedPoem");
    }

    #region private ================================================================================

    private ISKFunction GetMockFunction(string functionName)
    {
        return functionName switch
        {
            "ShortPoem" => this.GetShortPoemMockFunction(),
            "Translate" => this.GetTranslateMockFunction(),
            _ => new Mock<ISKFunction>().Object
        };
    }

    private ISKFunction GetShortPoemMockFunction()
    {
        var mockFunction = new Mock<ISKFunction>();

        mockFunction.Setup(x => x.Name).Returns("ShortPoem");
        mockFunction.Setup(x => x.SkillName).Returns("WriterSkill");
        mockFunction.Setup(x => x.Describe()).Returns(new FunctionView
        {
            Parameters = new List<ParameterView> { new ParameterView { Name = "input" } }
        });

        return mockFunction.Object;
    }

    private ISKFunction GetTranslateMockFunction()
    {
        var mockFunction = new Mock<ISKFunction>();

        mockFunction.Setup(x => x.Name).Returns("Translate");
        mockFunction.Setup(x => x.SkillName).Returns("WriterSkill");
        mockFunction.Setup(x => x.Describe()).Returns(new FunctionView
        {
            Parameters = new List<ParameterView>
            {
                new ParameterView { Name = "input" },
                new ParameterView { Name = "language" }
            }
        });

        return mockFunction.Object;
    }

    #endregion
}
