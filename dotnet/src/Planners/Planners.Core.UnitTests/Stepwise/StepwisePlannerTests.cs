// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Planners.Stepwise;
using Moq;
using Xunit;

namespace Microsoft.SemanticKernel.Planners.UnitTests.Stepwise;

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
        var planner = new StepwisePlanner(kernel.Object, config);

        // Assert
        getPromptTemplateMock.Verify(x => x(), Times.Once());
    }
}
