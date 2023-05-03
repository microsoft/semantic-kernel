// Copyright (c) Microsoft. All rights reserved.

using System;
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
        Assert.Throws<ArgumentException>(() => new FakeAIServiceConfig(string.Empty));
    }

    private sealed class FakeAIServiceConfig : ServiceConfig
    {
        public FakeAIServiceConfig(string serviceId) : base(serviceId)
        {
        }
    }
}
