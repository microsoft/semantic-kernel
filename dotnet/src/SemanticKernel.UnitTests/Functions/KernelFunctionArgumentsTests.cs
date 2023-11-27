// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;
public class KernelFunctionArgumentsTests
{
    [Fact]
    public void ItCanBeCreatedWithNoArguments()
    {
        KernelFunctionArguments sut = new() { };

        Assert.Null(sut.ExecutionSettings);
        Assert.Empty(sut);
    }

    [Fact]
    public void ItCanBeCreatedWithExecutionSettingsOnly()
    {
        // Arrange
        var executionSettings = new PromptExecutionSettings();

        // Act
        KernelFunctionArguments sut = new(executionSettings) { };

        // Assert
        Assert.Equal(executionSettings, sut.ExecutionSettings);
        Assert.Empty(sut);
    }

    [Fact]
    public void ItCanBeCreatedWithArgumentsOnly()
    {
        // Arrange & Act
        KernelFunctionArguments sut = new() { { "fake-key", "fake-value" } };

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
        KernelFunctionArguments sut = new(executionSettings) { { "fake-key", "fake-value" } };

        // Assert
        Assert.Equal(executionSettings, sut.ExecutionSettings);

        var argument = Assert.Single(sut);
        Assert.Equal("fake-key", argument.Key);
        Assert.Equal("fake-value", argument.Value);
    }

    [Fact]
    public void ItCanPerformCaseInsensitiveSearch()
    {
        //Constructor 1
        var executionSettings = new PromptExecutionSettings();
        KernelFunctionArguments sut = new(executionSettings) { { "FAKE-key", "fake-value" } };
        Assert.True(sut.ContainsKey("fake-key"));

        //Constructor 2
        IDictionary<string, string> source = new Dictionary<string, string> { { "FAKE-key", "fake-value" } };
        sut = new(source);
        Assert.True(sut.ContainsKey("fake-key"));

        //Constructor 3
        KernelFunctionArguments other = new() { { "FAKE-key", "fake-value" } };
        sut = new(other);
        Assert.True(sut.ContainsKey("fake-key"));
    }

    [Fact]
    public void ItCanBeInitializedFromIDictionary()
    {
        // Arrange
        IDictionary<string, string> source = new Dictionary<string, string> { { "fake-key", "fake-value" } };

        // Act
        KernelFunctionArguments sut = new(source);

        // Assert
        Assert.Single(sut);
        Assert.True(sut.ContainsKey("fake-key"));
        Assert.Equal("fake-value", sut["fake-key"]);

        Assert.Null(sut.ExecutionSettings);
    }

    [Fact]
    public void ItCanBeInitializedFromAnotherSettingsInstance()
    {
        // Arrange
        var executionSettings = new PromptExecutionSettings();
        var other = new KernelFunctionArguments(executionSettings) { { "Fake-key", "fake-value" } };

        // Act
        KernelFunctionArguments sut = new(other);

        // Assert
        Assert.Single(sut);
        Assert.True(sut.ContainsKey("fake-key"));
        Assert.Equal("fake-value", sut["fake-key"]);

        Assert.Equal(executionSettings, sut.ExecutionSettings);
    }
}
