// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Planning.Stepwise;
using Moq;
using Xunit;

namespace SemanticKernel.Extensions.UnitTests.Planning.StepwisePlanner;

public sealed class StepwisePlannerTests
{
    [Fact]
    public void UsesPromptDelegateWhenProvided()
    {
        // Arrange
        var kernel = new Mock<IKernel>();
        kernel.Setup(x => x.LoggerFactory).Returns(NullLoggerFactory.Instance);
        var getPromptTemplateMock = new Mock<Func<string>>();
        var config = new StepwisePlannerConfig()
        {
            GetPromptTemplate = getPromptTemplateMock.Object
        };

        // Act
        var planner = new Microsoft.SemanticKernel.Planning.StepwisePlanner(kernel.Object, config);

        // Assert
        getPromptTemplateMock.Verify(x => x(), Times.Once());
    }
}
