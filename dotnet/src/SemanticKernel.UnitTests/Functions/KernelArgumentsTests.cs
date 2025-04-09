// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public class KernelArgumentsTests
{
    [Fact]
    public void ItCanBeCreatedWithNoArguments()
    {
        KernelArguments sut = [];

        Assert.Null(sut.ExecutionSettings);
        Assert.Empty(sut);
    }

    [Fact]
    public void ItCanBeCreatedWithExecutionSettingsOnly()
    {
        // Arrange
        var executionSettings = new PromptExecutionSettings();

        // Act
        KernelArguments sut = new(executionSettings) { };

        // Assert
        Assert.Same(executionSettings, sut.ExecutionSettings?[PromptExecutionSettings.DefaultServiceId]);
        Assert.Empty(sut);
    }

    [Fact]
    public void ItCanBeCreatedWithArgumentsOnly()
    {
        // Arrange & Act
        KernelArguments sut = new() { { "fake-key", "fake-value" } };

        // Assert
        Assert.Null(sut.ExecutionSettings);

        var argument = Assert.Single(sut);
        Assert.Equal("fake-key", argument.Key);
        Assert.Equal("fake-value", argument.Value);
    }

    [Fact]
    public void ItCanBeCreatedWithBothExecutionSettingsAndArguments()
    {
        // Arrange
        var executionSettings = new PromptExecutionSettings();

        // Act
        KernelArguments sut = new(executionSettings) { { "fake-key", "fake-value" } };

        // Assert
        Assert.Same(executionSettings, sut.ExecutionSettings?[PromptExecutionSettings.DefaultServiceId]);

        var argument = Assert.Single(sut);
        Assert.Equal("fake-key", argument.Key);
        Assert.Equal("fake-value", argument.Value);
    }

    [Fact]
    public void ItCanBeCreatedWithMultipleExecutionSettingsAndArguments()
    {
        // Arrange
        var executionSettings1 = new PromptExecutionSettings();
        var executionSettings2 = new PromptExecutionSettings() { ServiceId = "service-2" };
        var executionSettings3 = new PromptExecutionSettings() { ServiceId = "service-3" };

        // Act
        KernelArguments sut = new([executionSettings1, executionSettings2, executionSettings3]) { { "fake-key", "fake-value" } };

        // Assert
        Assert.Same(executionSettings1, sut.ExecutionSettings?[PromptExecutionSettings.DefaultServiceId]);
        Assert.Same(executionSettings2, sut.ExecutionSettings?["service-2"]);
        Assert.Same(executionSettings3, sut.ExecutionSettings?["service-3"]);

        var argument = Assert.Single(sut);
        Assert.Equal("fake-key", argument.Key);
        Assert.Equal("fake-value", argument.Value);
    }

    [Theory]
    [InlineData(null, null)]
    [InlineData("default", null)]
    [InlineData(null, "default")]
    [InlineData("service1", null, "service1")]
    [InlineData(null, "service2", "service2")]
    [InlineData("service1", "service2", "service3", null, "service1")]
    public void ItCannotBeCreatedWithMultipleExecutionSettingsWithClashingServiceIdOrWithoutServiceIdSet(params string?[] serviceIds)
    {
        // Arrange
        var executionSettingsList = serviceIds?.Select(serviceId => new PromptExecutionSettings() { ServiceId = serviceId }).ToList();

        // Act & Assert
        Assert.Throws<ArgumentException>(() => new KernelArguments(executionSettingsList) { { "fake-key", "fake-value" } });
    }

    [Fact]
    public void ItCanPerformCaseInsensitiveSearch()
    {
        //Constructor 1
        var executionSettings = new PromptExecutionSettings();
        KernelArguments sut = new(executionSettings) { { "FAKE-key", "fake-value" } };
        Assert.True(sut.ContainsName("fake-key"));

        //Constructor 2
        IDictionary<string, object?> source = new Dictionary<string, object?> { { "FAKE-key", "fake-value" } };
        sut = new(source);
        Assert.True(sut.ContainsName("fake-key"));

        //Constructor 3
        KernelArguments other = new() { { "FAKE-key", "fake-value" } };
        sut = new(other);
        Assert.True(sut.ContainsName("fake-key"));
    }

    [Fact]
    public void ItCanBeInitializedFromIDictionary()
    {
        // Arrange
        IDictionary<string, object?> source = new Dictionary<string, object?> { { "fake-key", "fake-value" } };

        // Act
        KernelArguments sut = new(source);

        // Assert
        Assert.Single(sut);
        Assert.True(sut.ContainsName("fake-key"));
        Assert.Equal("fake-value", sut["fake-key"]);

        Assert.Null(sut.ExecutionSettings);
    }

    [Fact]
    public void ItCanBeInitializedFromAnotherSettingsInstance()
    {
        // Arrange
        var executionSettings = new PromptExecutionSettings();
        var other = new KernelArguments(executionSettings) { { "Fake-key", "fake-value" } };

        // Act
        KernelArguments sut = new(other);

        // Assert
        Assert.Single(sut);
        Assert.True(sut.ContainsName("fake-key"));
        Assert.Equal("fake-value", sut["fake-key"]);

        Assert.Same(executionSettings, sut.ExecutionSettings?[PromptExecutionSettings.DefaultServiceId]);
    }
}
