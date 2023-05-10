// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.SkillDefinition;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.SkillDefinition;

public class SkillCollectionTests
{
    [Fact]
    public void ItShouldDisposeSkillsFunctions()
    {
        // Arrange
        var disposableFunction = new Mock<ISKFunction>();
        disposableFunction.SetupGet(f => f.Name).Returns("fake-function-name");
        disposableFunction.SetupGet(f => f.SkillName).Returns("fake-skill-name");
        disposableFunction.As<IDisposable>();

        var skillsCollection = new SkillCollection();
        skillsCollection.AddNativeFunction(disposableFunction.Object);

        //Act
        skillsCollection.Dispose();

        //Assert
        disposableFunction.As<IDisposable>().Verify(f => f.Dispose(), Times.Once);
    }
}
