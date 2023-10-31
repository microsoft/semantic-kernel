// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging.Abstractions;
using Moq;
using Xunit;

#pragma warning disable IDE0130 // Namespace does not match folder structure
namespace Microsoft.SemanticKernel.Planners.Stepwise.UnitTests;
#pragma warning restore IDE0130 // Namespace does not match folder structure

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
