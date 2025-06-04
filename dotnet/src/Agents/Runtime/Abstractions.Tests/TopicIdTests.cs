// Copyright (c) Microsoft. All rights reserved.

using System;
using Xunit;

namespace Microsoft.SemanticKernel.Agents.Runtime.Abstractions.Tests;

[Trait("Category", "Unit")]
public class TopicIdTests
{
    [Fact]
    public void ConstrWithTypeOnlyTest()
    {
        // Arrange & Act
        TopicId topicId = new("testtype");

        // Assert
        Assert.Equal("testtype", topicId.Type);
        Assert.Equal(TopicId.DefaultSource, topicId.Source);
    }

    [Fact]
    public void ConstructWithTypeAndSourceTest()
    {
        // Arrange & Act
        TopicId topicId = new("testtype", "customsource");

        // Assert
        Assert.Equal("testtype", topicId.Type);
        Assert.Equal("customsource", topicId.Source);
    }

    [Fact]
    public void ConstructWithTupleTest()
    {
        // Arrange
        (string, string) tuple = ("testtype", "customsource");

        // Act
        TopicId topicId = new(tuple);

        // Assert
        Assert.Equal("testtype", topicId.Type);
        Assert.Equal("customsource", topicId.Source);
    }

    [Fact]
    public void ConvertFromStringTest()
    {
        // Arrange
        const string topicIdStr = "testtype/customsource";

        // Act
        TopicId topicId = TopicId.FromStr(topicIdStr);

        // Assert
        Assert.Equal("testtype", topicId.Type);
        Assert.Equal("customsource", topicId.Source);
    }

    [Theory]
    [InlineData("invalid-format")]
    [InlineData("too/many/parts")]
    [InlineData("")]
    public void InvalidFormatFromStringThrowsTest(string invalidInput)
    {
        // Act & Assert
        Assert.Throws<FormatException>(() => TopicId.FromStr(invalidInput));
    }

    [Fact]
    public void ToStringTest()
    {
        // Arrange
        TopicId topicId = new("testtype", "customsource");

        // Act
        string result = topicId.ToString();

        // Assert
        Assert.Equal("testtype/customsource", result);
    }

    [Fact]
    public void EqualityTest()
    {
        // Arrange
        TopicId topicId1 = new("testtype", "customsource");
        TopicId topicId2 = new("testtype", "customsource");

        // Act & Assert
        Assert.True(topicId1.Equals(topicId2));
        Assert.True(topicId1.Equals((object)topicId2));
    }

    [Fact]
    public void InequalityTest()
    {
        // Arrange
        TopicId topicId1 = new("testtype1", "source1");
        TopicId topicId2 = new("testtype2", "source2");
        TopicId topicId3 = new("testtype1", "source2");
        TopicId topicId4 = new("testtype2", "source1");

        // Act & Assert
        Assert.False(topicId1.Equals(topicId2));
        Assert.False(topicId1.Equals(topicId3));
        Assert.False(topicId1.Equals(topicId4));
    }

    [Fact]
    public void NullEqualityTest()
    {
        // Arrange
        TopicId topicId = new("testtype", "customsource");

        // Act & Assert
        Assert.False(topicId.Equals(null));
    }

    [Fact]
    public void DifferentTypeEqualityTest()
    {
        // Arrange
        TopicId topicId = new("testtype", "customsource");
        const string differentType = "not-a-topic-id";

        // Act & Assert
        Assert.False(topicId.Equals(differentType));
    }

    [Fact]
    public void GetHashCodeTest()
    {
        // Arrange
        TopicId topicId1 = new("testtype", "customsource");
        TopicId topicId2 = new("testtype", "customsource");

        // Act
        int hash1 = topicId1.GetHashCode();
        int hash2 = topicId2.GetHashCode();

        // Assert
        Assert.Equal(hash1, hash2);
    }

    [Fact]
    public void ExplicitConversionTest()
    {
        // Arrange
        string topicIdStr = "testtype/customsource";

        // Act
        TopicId topicId = (TopicId)topicIdStr;

        // Assert
        Assert.Equal("testtype", topicId.Type);
        Assert.Equal("customsource", topicId.Source);
    }

    [Fact]
    public void IsWildcardMatchTest()
    {
        // Arrange
        TopicId topicId1 = new("testtype", "source1");
        TopicId topicId2 = new("testtype", "source2");

        // Act & Assert
        Assert.True(topicId1.IsWildcardMatch(topicId2));
        Assert.True(topicId2.IsWildcardMatch(topicId1));
    }

    [Fact]
    public void IsWildcardMismatchTest()
    {
        // Arrange
        TopicId topicId1 = new("testtype1", "source");
        TopicId topicId2 = new("testtype2", "source");

        // Act & Assert
        Assert.False(topicId1.IsWildcardMatch(topicId2));
        Assert.False(topicId2.IsWildcardMatch(topicId1));
    }
}
