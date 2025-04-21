// Copyright (c) Microsoft. All rights reserved.

using System;
using FluentAssertions;
using Xunit;

namespace Microsoft.SemanticKernel.Agents.Runtime.Abstractions.Tests;

[Trait("Category", "Unit")]
public class AgentIdTests()
{
    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData(" ")]
    [InlineData("invalid\u007Fkey")] // DEL character (127) is outside ASCII 32-126 range
    [InlineData("invalid\u0000key")] // NULL character is outside ASCII 32-126 range
    [InlineData("invalid\u0010key")] // Control character is outside ASCII 32-126 range
    [InlineData("InvalidKey💀")] // Control character is outside ASCII 32-126 range
    public void AgentIdShouldThrowArgumentExceptionWithInvalidKey(string? invalidKey)
    {
        // Act & Assert
        ArgumentException exception = Assert.Throws<ArgumentException>(() => new AgentId("validType", invalidKey!));
        Assert.Contains("Invalid AgentId key", exception.Message);
    }

    [Fact]
    public void AgentIdShouldInitializeCorrectlyTest()
    {
        AgentId agentId = new("TestType", "TestKey");

        agentId.Type.Should().Be("TestType");
        agentId.Key.Should().Be("TestKey");
    }

    [Fact]
    public void AgentIdShouldConvertFromTupleTest()
    {
        (string, string) agentTuple = ("TupleType", "TupleKey");
        AgentId agentId = new(agentTuple);

        agentId.Type.Should().Be("TupleType");
        agentId.Key.Should().Be("TupleKey");
    }

    [Fact]
    public void AgentIdShouldConvertFromAgentType()
    {
        AgentType agentType = "TestType";
        AgentId agentId = new(agentType, "TestKey");

        agentId.Type.Should().Be("TestType");
        agentId.Key.Should().Be("TestKey");
    }

    [Fact]
    public void AgentIdShouldParseFromStringTest()
    {
        AgentId agentId = AgentId.FromStr("ParsedType/ParsedKey");

        agentId.Type.Should().Be("ParsedType");
        agentId.Key.Should().Be("ParsedKey");
    }

    [Fact]
    public void AgentIdShouldCompareEqualityCorrectlyTest()
    {
        AgentId agentId1 = new("SameType", "SameKey");
        AgentId agentId2 = new("SameType", "SameKey");
        AgentId agentId3 = new("DifferentType", "DifferentKey");

        agentId1.Should().Be(agentId2);
        agentId1.Should().NotBe(agentId3);
        (agentId1 == agentId2).Should().BeTrue();
        (agentId1 != agentId3).Should().BeTrue();
    }

    [Fact]
    public void AgentIdShouldGenerateCorrectHashCodeTest()
    {
        AgentId agentId1 = new("HashType", "HashKey");
        AgentId agentId2 = new("HashType", "HashKey");
        AgentId agentId3 = new("DifferentType", "DifferentKey");

        agentId1.GetHashCode().Should().Be(agentId2.GetHashCode());
        agentId1.GetHashCode().Should().NotBe(agentId3.GetHashCode());
    }

    [Fact]
    public void AgentIdShouldConvertExplicitlyFromStringTest()
    {
        AgentId agentId = (AgentId)"ConvertedType/ConvertedKey";

        agentId.Type.Should().Be("ConvertedType");
        agentId.Key.Should().Be("ConvertedKey");
    }

    [Fact]
    public void AgentIdShouldReturnCorrectToStringTest()
    {
        AgentId agentId = new("ToStringType", "ToStringKey");

        agentId.ToString().Should().Be("ToStringType/ToStringKey");
    }

    [Fact]
    public void AgentIdShouldCompareInequalityForWrongTypeTest()
    {
        AgentId agentId1 = new("Type1", "Key1");

        (!agentId1.Equals(Guid.NewGuid())).Should().BeTrue();
    }

    [Fact]
    public void AgentIdShouldCompareInequalityCorrectlyTest()
    {
        AgentId agentId1 = new("Type1", "Key1");
        AgentId agentId2 = new("Type2", "Key2");

        (agentId1 != agentId2).Should().BeTrue();
    }
}
