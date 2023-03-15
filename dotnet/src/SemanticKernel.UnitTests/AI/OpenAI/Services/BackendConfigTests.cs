// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.AI.OpenAI.Services;
using Microsoft.SemanticKernel.Diagnostics;
using Xunit;

namespace SemanticKernel.UnitTests.AI.OpenAI.Services;

public class BackendConfigTests
{
    [Fact]
    public void ConstructorWithValidParametersSetsProperties()
    {
        // Arrange
        string label = "testLabel";

        // Act
        var config = new FakeBackendConfig(label);

        // Assert
        Assert.Equal(label, config.Label);
    }

    [Fact]
    public void ConstructorWithEmptyRequiredParameterThrowsArgumentException()
    {
        // Act + Assert
        var exception = Assert.Throws<ValidationException>(() => new FakeBackendConfig(string.Empty));

        Assert.Equal(ValidationException.ErrorCodes.EmptyValue, exception?.ErrorCode);
    }

    private class FakeBackendConfig : BackendConfig
    {
        public FakeBackendConfig(string label) : base(label)
        {
        }
    }
}
