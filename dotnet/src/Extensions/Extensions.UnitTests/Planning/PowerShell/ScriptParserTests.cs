// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.Planning.PowerShell;
using Microsoft.SemanticKernel.SkillDefinition;
using Moq;
using Xunit;

namespace SemanticKernel.Extensions.UnitTests.Planning.PowerShell;

public class ScriptParserTests
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
        var plan = ScriptParser.ToPlanFromScript(Script, Goal, (skillName, functionName) => this.GetMockFunction(functionName));

        // Assert
        Assert.Equal(Goal, plan.Description);
        Assert.Equal(Script, plan.OriginalPlan);

        Assert.Equal(2, plan.Steps.Count);
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

        mockFunction.Setup(x => x.Describe()).Returns(new FunctionView
        {
            Name = "ShortPoem",
            SkillName = "WriterSkill",
            Parameters = new List<ParameterView> { new ParameterView { Name = "input" } }
        });

        return mockFunction.Object;
    }

    private ISKFunction GetTranslateMockFunction()
    {
        var mockFunction = new Mock<ISKFunction>();

        mockFunction.Setup(x => x.Describe()).Returns(new FunctionView
        {
            Name = "Translate",
            SkillName = "WriterSkill",
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
