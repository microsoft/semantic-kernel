// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Reflection;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SemanticFunctions;
using Microsoft.SemanticKernel.SkillDefinition;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.SkillDefinition;
public class SkillCollectionTests
{
    private readonly Mock<IPromptTemplate> _promptTemplate;
    private readonly SemanticFunctionConfig _semanticFunctionConfig;

    public SkillCollectionTests()
    {
        this._promptTemplate = new Mock<IPromptTemplate>();
        this._promptTemplate.Setup(x => x.RenderAsync(It.IsAny<SKContext>())).ReturnsAsync("foo");
        this._promptTemplate.Setup(x => x.GetParameters()).Returns(new List<ParameterView>());

        var templateConfig = new PromptTemplateConfig();
        this._semanticFunctionConfig = new SemanticFunctionConfig(templateConfig, this._promptTemplate.Object);
    }

    [Fact]
    public void ItReturnsAllRegisteredFunctions()
    {
        //Arrange
        var semanticFunction = SKFunction.FromSemanticConfig("sk", "name", this._semanticFunctionConfig);
        var nativeFunction = SKFunction.FromNativeMethod(typeof(SkillCollectionTests).GetMethod(nameof(TestNativeFunction), BindingFlags.Static | BindingFlags.NonPublic));

        var sut = new SkillCollection();
        sut.AddSemanticFunction(semanticFunction);
        sut.AddNativeFunction(nativeFunction);

        // Act
        var allFunctions = sut.GetAllFunctions();

        //Assert
        Assert.Equal(2, allFunctions.Count);
        Assert.Contains(allFunctions, f => f.IsSemantic == true);
        Assert.Contains(allFunctions, f => f.IsSemantic == false);
    }

    [SKFunction("TestNativeFunction")]
    private static Task TestNativeFunction(SKContext context)
    {
        return Task.FromResult(0);
    }
}
