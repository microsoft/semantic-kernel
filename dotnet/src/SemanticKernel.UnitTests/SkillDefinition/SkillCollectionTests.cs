// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.SkillDefinition;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.SkillDefinition;

public class SkillCollectionTests
{
    [Fact]
    public void ItAllowsToReplaceFunctions()
    {
        // Arrange
        var functionOne = new Mock<ISKFunction>();
        functionOne.SetupGet(x => x.Name).Returns("fName");
        functionOne.SetupGet(x => x.SkillName).Returns("sName");
        functionOne.SetupGet(x => x.Description).Returns("ONE");
        functionOne.SetupGet(x => x.IsSemantic).Returns(false);
        functionOne.SetupGet(x => x.RequestSettings).Returns(new CompleteRequestSettings());

        var functionTwo = new Mock<ISKFunction>();
        functionTwo.SetupGet(x => x.Name).Returns("fName");
        functionTwo.SetupGet(x => x.SkillName).Returns("sName");
        functionTwo.SetupGet(x => x.Description).Returns("TWO");
        functionTwo.SetupGet(x => x.IsSemantic).Returns(false);
        functionTwo.SetupGet(x => x.RequestSettings).Returns(new CompleteRequestSettings());

        using var target = new SkillCollection();

        // Act
        target.AddFunction(functionOne.Object);

        // Assert
        Assert.True(target.TryGetFunction("sName", "fName", out var func));
        Assert.Equal("ONE", func.Description);

        // Act
        target.AddFunction(functionTwo.Object);

        // Assert
        Assert.True(target.TryGetFunction("sName", "fName", out func));
        Assert.Equal("TWO", func.Description);
    }

    [Fact]
    public void ItShouldDisposeSkillsFunctions()
    {
        // Arrange
        var disposableFunction = new Mock<ISKFunction>();
        disposableFunction.SetupGet(f => f.Name).Returns("fake-function-name");
        disposableFunction.SetupGet(f => f.SkillName).Returns("fake-skill-name");
        disposableFunction.As<IDisposable>();

        var skillsCollection = new SkillCollection();
        skillsCollection.AddFunction(disposableFunction.Object);

        //Act
        skillsCollection.Dispose();

        //Assert
        disposableFunction.As<IDisposable>().Verify(f => f.Dispose(), Times.Once);
    }
}
