// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public class FunctionCollectionTests
{
    [Fact]
    public void ItAllowsToReplaceFunctions()
    {
        // Arrange
        List<AIRequestSettings> modelSettings = new();
        modelSettings.Add(new AIRequestSettings());

        var functionOne = new Mock<ISKFunction>();
        functionOne.SetupGet(x => x.Name).Returns("fName");
        functionOne.SetupGet(x => x.PluginName).Returns("sName");
        functionOne.SetupGet(x => x.Description).Returns("ONE");

        var functionTwo = new Mock<ISKFunction>();
        functionTwo.SetupGet(x => x.Name).Returns("fName");
        functionTwo.SetupGet(x => x.PluginName).Returns("sName");
        functionTwo.SetupGet(x => x.Description).Returns("TWO");

        var target = new FunctionCollection();

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
}
