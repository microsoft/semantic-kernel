// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Orchestration;
using Moq;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Orchestration;

/// <summary>
/// Unit tests for the <see cref="OrchestrationTarget"/> class.
/// </summary>
public sealed class OrchestrationTargetTests
{
    [Fact]
    public void ConstructWithAgent_SetsCorrectProperties()
    {
        // Arrange
        Mock<Agent> mockAgent = new(MockBehavior.Strict);

        // Act
        OrchestrationTarget target = new(mockAgent.Object);

        // Assert
        Assert.Equal(OrchestrationTargetType.Agent, target.TargetType);
        Assert.Same(mockAgent.Object, target.Agent);
        Assert.Null(target.Orchestration);
    }

    [Fact]
    public void ConstructWithOrchestration_SetsCorrectProperties()
    {
        // Arrange
        Mock<Orchestratable> mockOrchestration = new(MockBehavior.Strict);

        // Act
        OrchestrationTarget target = new(mockOrchestration.Object);

        // Assert
        Assert.Equal(OrchestrationTargetType.Orchestratable, target.TargetType);
        Assert.Same(mockOrchestration.Object, target.Orchestration);
        Assert.Null(target.Agent);
    }

    [Fact]
    public void ImplicitConversionFromAgent_CreatesValidTarget()
    {
        // Arrange
        Mock<Agent> mockAgent = new(MockBehavior.Strict);

        // Act
        OrchestrationTarget target = mockAgent.Object;

        // Assert
        Assert.Equal(OrchestrationTargetType.Agent, target.TargetType);
        Assert.Same(mockAgent.Object, target.Agent);
    }

    [Fact]
    public void ImplicitConversionFromOrchestration_CreatesValidTarget()
    {
        // Arrange
        Mock<Orchestratable> mockOrchestration = new(MockBehavior.Strict);

        // Act
        OrchestrationTarget target = mockOrchestration.Object;

        // Assert
        Assert.Equal(OrchestrationTargetType.Orchestratable, target.TargetType);
        Assert.Same(mockOrchestration.Object, target.Orchestration);
    }

    [Fact]
    public void IsAgent_ReturnsTrueAndAgent_WhenTargetIsAgent()
    {
        // Arrange
        Mock<Agent> mockAgent = new(MockBehavior.Strict);
        OrchestrationTarget target = new(mockAgent.Object);

        // Act
        bool isAgent = target.IsAgent(out Agent? agent);

        // Assert
        Assert.True(isAgent);
        Assert.Same(mockAgent.Object, agent);
    }

    [Fact]
    public void IsAgent_ReturnsFalseAndNull_WhenTargetIsNotAgent()
    {
        // Arrange
        Mock<Orchestratable> mockOrchestration = new(MockBehavior.Strict);
        OrchestrationTarget target = new(mockOrchestration.Object);

        // Act
        bool isAgent = target.IsAgent(out Agent? agent);

        // Assert
        Assert.False(isAgent);
        Assert.Null(agent);
    }

    [Fact]
    public void IsOrchestration_ReturnsTrueAndOrchestration_WhenTargetIsOrchestration()
    {
        // Arrange
        Mock<Orchestratable> mockOrchestration = new(MockBehavior.Strict);
        OrchestrationTarget target = new(mockOrchestration.Object);

        // Act
        bool isOrchestration = target.IsOrchestration(out Orchestratable? orchestration);

        // Assert
        Assert.True(isOrchestration);
        Assert.Same(mockOrchestration.Object, orchestration);
    }

    [Fact]
    public void IsOrchestration_ReturnsFalseAndNull_WhenTargetIsNotOrchestration()
    {
        // Arrange
        Mock<Agent> mockAgent = new(MockBehavior.Strict);
        OrchestrationTarget target = new(mockAgent.Object);

        // Act
        bool isOrchestration = target.IsOrchestration(out Orchestratable? orchestration);

        // Assert
        Assert.False(isOrchestration);
        Assert.Null(orchestration);
    }

    [Fact]
    public void Equals_ReturnsTrueForSameAgentReference()
    {
        // Arrange
        Mock<Agent> mockAgent = new(MockBehavior.Strict);
        OrchestrationTarget target1 = new(mockAgent.Object);
        OrchestrationTarget target2 = new(mockAgent.Object);

        // Act & Assert
        Assert.True(target1.Equals(target2));
        Assert.True(target1 == target2);
        Assert.False(target1 != target2);
    }

    [Fact]
    public void Equals_ReturnsTrueForSameOrchestrationReference()
    {
        // Arrange
        Mock<Orchestratable> mockOrchestration = new(MockBehavior.Strict);
        OrchestrationTarget target1 = new(mockOrchestration.Object);
        OrchestrationTarget target2 = new(mockOrchestration.Object);

        // Act & Assert
        Assert.True(target1.Equals(target2));
        Assert.True(target1 == target2);
        Assert.False(target1 != target2);
    }

    [Fact]
    public void Equals_ReturnsFalseForDifferentReferences()
    {
        // Arrange
        Mock<Agent> mockAgent1 = new(MockBehavior.Strict);
        Mock<Agent> mockAgent2 = new(MockBehavior.Strict);
        OrchestrationTarget target1 = new(mockAgent1.Object);
        OrchestrationTarget target2 = new(mockAgent2.Object);

        // Act & Assert
        Assert.False(target1.Equals(target2));
        Assert.False(target1 == target2);
        Assert.True(target1 != target2);
    }

    [Fact]
    public void Equals_ReturnsFalseForDifferentTypes()
    {
        // Arrange
        Mock<Agent> mockAgent = new(MockBehavior.Strict);
        Mock<Orchestratable> mockOrchestration = new(MockBehavior.Strict);
        OrchestrationTarget target1 = new(mockAgent.Object);
        OrchestrationTarget target2 = new(mockOrchestration.Object);

        // Act & Assert
        Assert.False(target1.Equals(target2));
        Assert.False(target1 == target2);
        Assert.True(target1 != target2);
    }

    [Fact]
    public void GetHashCode_ReturnsSameValueForEqualObjects()
    {
        // Arrange
        Mock<Agent> mockAgent = new(MockBehavior.Strict);
        OrchestrationTarget target1 = new(mockAgent.Object);
        OrchestrationTarget target2 = new(mockAgent.Object);

        // Act
        int hashCode1 = target1.GetHashCode();
        int hashCode2 = target2.GetHashCode();

        // Assert
        Assert.Equal(hashCode1, hashCode2);
    }

    [Fact]
    public void GetHashCode_ReturnsDifferentValuesForDifferentObjects()
    {
        // Arrange
        Mock<Agent> mockAgent = new(MockBehavior.Strict);
        Mock<Orchestratable> mockOrchestration = new(MockBehavior.Strict);
        OrchestrationTarget target1 = new(mockAgent.Object);
        OrchestrationTarget target2 = new(mockOrchestration.Object);

        // Act
        int hashCode1 = target1.GetHashCode();
        int hashCode2 = target2.GetHashCode();

        // Assert
        Assert.NotEqual(hashCode1, hashCode2);
    }
}
