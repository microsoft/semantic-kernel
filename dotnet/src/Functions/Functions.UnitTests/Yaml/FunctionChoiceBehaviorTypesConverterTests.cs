// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using Microsoft.SemanticKernel;
using Xunit;
using YamlDotNet.Serialization;
using YamlDotNet.Serialization.NamingConventions;

namespace SemanticKernel.Functions.UnitTests.Yaml;

/// <summary>
/// Tests for <see cref="FunctionChoiceBehaviorTypesConverter"/>.
/// </summary>
public sealed class FunctionChoiceBehaviorTypesConverterTests
{
    [Fact]
    public void ItShouldDeserializeAutoFunctionChoiceBehavior()
    {
        // Arrange
        var deserializer = new DeserializerBuilder()
            .WithNamingConvention(UnderscoredNamingConvention.Instance)
            .WithTypeConverter(new FunctionChoiceBehaviorTypesConverter())
            .Build();

        var yaml = """
            type: auto
            functions:
            - p1.f1
            """;

        // Act
        var behavior = deserializer.Deserialize<AutoFunctionChoiceBehavior>(yaml);

        // Assert
        Assert.NotNull(behavior.Functions);
        Assert.Single(behavior.Functions);
        Assert.Equal("p1-f1", behavior.Functions.Single());
    }

    [Fact]
    public void ItShouldDeserializeRequiredFunctionChoiceBehavior()
    {
        // Arrange
        var deserializer = new DeserializerBuilder()
            .WithNamingConvention(UnderscoredNamingConvention.Instance)
            .WithTypeConverter(new FunctionChoiceBehaviorTypesConverter())
            .Build();

        var yaml = """
            type: required
            functions:
            - p2.f2
            """;

        // Act
        var behavior = deserializer.Deserialize<RequiredFunctionChoiceBehavior>(yaml);

        // Assert
        Assert.NotNull(behavior.Functions);
        Assert.Single(behavior.Functions);
        Assert.Equal("p2-f2", behavior.Functions.Single());
    }

    [Fact]
    public void ItShouldDeserializeNoneFunctionChoiceBehavior()
    {
        // Arrange
        var deserializer = new DeserializerBuilder()
            .WithNamingConvention(UnderscoredNamingConvention.Instance)
            .WithTypeConverter(new FunctionChoiceBehaviorTypesConverter())
            .Build();

        var yaml = """
            type: none,
            functions:
            - p1.f1
            """;

        // Act
        var behavior = deserializer.Deserialize<NoneFunctionChoiceBehavior>(yaml);

        // Assert
        Assert.NotNull(behavior.Functions);
        Assert.Single(behavior.Functions);
        Assert.Equal("p1-f1", behavior.Functions.Single());
    }
}
