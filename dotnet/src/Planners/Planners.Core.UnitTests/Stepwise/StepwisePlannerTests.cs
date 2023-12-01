// Copyright (c) Microsoft. All rights reserved.

using Moq;
using Xunit;

namespace Microsoft.SemanticKernel.Planning.Stepwise.UnitTests;

public sealed class StepwisePlannerTests
{
    [Fact]
    public void UsesPromptDelegateWhenProvided()
    {
        // Arrange
        var kernel = new Kernel(new Mock<IServiceProvider>().Object);

        var getPromptTemplateMock = new Mock<Func<string>>();
        var config = new StepwisePlannerConfig()
        {
            GetPromptTemplate = getPromptTemplateMock.Object
        };

        // Act
        var planner = new StepwisePlanner(kernel, config);

        // Assert
        getPromptTemplateMock.Verify(x => x(), Times.Once());
    }
}
