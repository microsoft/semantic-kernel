// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Services;
using Xunit;

namespace SemanticKernel.UnitTests.Services;

public class ServiceConfigTests
{
    [Fact]
    public void ConstructorWithValidParametersSetsProperties()
    {
        // Arrange
        string serviceId = "testId";

        // Act
        var config = new FakeAIServiceConfig(serviceId);

        // Assert
        Assert.Equal(serviceId, config.ServiceId);
    }

    [Fact]
    public void ConstructorWithEmptyRequiredParameterThrowsArgumentException()
    {
        // Act + Assert
        var exception = Assert.Throws<ValidationException>(() => new FakeAIServiceConfig(string.Empty));

        Assert.Equal(ValidationException.ErrorCodes.EmptyValue, exception?.ErrorCode);
    }

    private class FakeAIServiceConfig : ServiceConfig
    {
        public FakeAIServiceConfig(string serviceId) : base(serviceId)
        {
        }
    }
}
