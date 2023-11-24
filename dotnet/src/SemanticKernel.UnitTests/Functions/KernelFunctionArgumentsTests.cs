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

        Assert.Null(sut.RequestSettings);
        Assert.Empty(sut);
    }

    [Fact]
    public void ItCanBeCreatedWithRequestSettingsOnly()
    {
        // Arrange
        var requestSettings = new AIRequestSettings();

        // Act
        KernelFunctionArguments sut = new(requestSettings) { };

        // Assert
        Assert.Equal(requestSettings, sut.RequestSettings);
        Assert.Empty(sut);
    }

    [Fact]
    public void ItCanBeCreatedWithArgumentsOnly()
    {
        // Arrange & Act
        KernelFunctionArguments sut = new() { { "fake-key", "fake-value" } };

        // Assert
        Assert.Null(sut.RequestSettings);

        var argument = Assert.Single(sut);
        Assert.Equal("fake-key", argument.Key);
        Assert.Equal("fake-value", argument.Value);
    }

    [Fact]
    public void ItCanBeCreatedWithBothRequestSettingsAndArguments()
    {
        // Arrange
        var requestSettings = new AIRequestSettings();

        // Act
        KernelFunctionArguments sut = new(requestSettings) { { "fake-key", "fake-value" } };

        // Assert
        Assert.Equal(requestSettings, sut.RequestSettings);

        var argument = Assert.Single(sut);
        Assert.Equal("fake-key", argument.Key);
        Assert.Equal("fake-value", argument.Value);
    }

    [Fact]
    public void ItCanPerformCaseInsensitiveSearch()
    {
        //Constructor 1
        var requestSettings = new AIRequestSettings();
        KernelFunctionArguments sut = new(requestSettings) { { "FAKE-key", "fake-value" } };
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

        Assert.Null(sut.RequestSettings);
    }

    [Fact]
    public void ItCanBeInitializedFromAnotherSettingsInstance()
    {
        // Arrange
        var requestSettings = new AIRequestSettings();
        var other = new KernelFunctionArguments(requestSettings) { { "Fake-key", "fake-value" } };

        // Act
        KernelFunctionArguments sut = new(other);

        // Assert
        Assert.Single(sut);
        Assert.True(sut.ContainsKey("fake-key"));
        Assert.Equal("fake-value", sut["fake-key"]);

        Assert.Equal(requestSettings, sut.RequestSettings);
    }
}
