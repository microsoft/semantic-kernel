// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Orchestration.Handoff;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Orchestration;

public class HandoffsTests
{
    [Fact]
    public void EmptyConstructors_CreateEmptyCollections()
    {
        AgentHandoffs agentHandoffs = [];
        Assert.Empty(agentHandoffs);

        OrchestrationHandoffs orchestrationHandoffs = [];
        Assert.Empty(orchestrationHandoffs);
    }

    [Fact]
    public void DictionaryConstructors_CopyValues()
    {
        Dictionary<string, string> handoffDict = new()
        {
            { "agent1", "description1" },
            { "agent2", "description2" }
        };

        AgentHandoffs agentHandoffs = new(handoffDict);
        Assert.Equal(2, agentHandoffs.Count);
        Assert.Equal("description1", agentHandoffs["agent1"]);
        Assert.Equal("description2", agentHandoffs["agent2"]);

        Dictionary<string, AgentHandoffs> orchestrationDict = new()
        {
            { "source1", new AgentHandoffs(handoffDict) }
        };

        OrchestrationHandoffs orchestrationHandoffs = new(orchestrationDict);
        Assert.Single(orchestrationHandoffs);
        Assert.Equal(2, orchestrationHandoffs["source1"].Count);
    }

    [Fact]
    public void Add_WithAgentObjects_CreatesHandoffRelationships()
    {
        // Arrange
        OrchestrationHandoffs handoffs = [];

        Agent sourceAgent = CreateAgent("source", "Source Agent");
        Agent targetAgent1 = CreateAgent("target1", "Target Agent 1");
        Agent targetAgent2 = CreateAgent("target2", "Target Agent 2");

        // Act
        handoffs.Add(sourceAgent, targetAgent1, targetAgent2);

        // Assert
        Assert.Single(handoffs);
        Assert.True(handoffs.ContainsKey("source"));

        AgentHandoffs sourceHandoffs = handoffs["source"];
        Assert.Equal(2, sourceHandoffs.Count);
        Assert.Equal("Target Agent 1", sourceHandoffs["target1"]);
        Assert.Equal("Target Agent 2", sourceHandoffs["target2"]);
    }

    [Fact]
    public void Add_WithAgentAndCustomDescription_UsesCustomDescription()
    {
        // Arrange
        OrchestrationHandoffs handoffs = [];

        Agent sourceAgent = CreateAgent("source", "Source Agent");
        Agent targetAgent = CreateAgent("target", "Target Agent");
        string customDescription = "Custom handoff description";

        // Act
        handoffs.Add(sourceAgent, targetAgent, customDescription);

        // Assert
        Assert.Single(handoffs);
        AgentHandoffs sourceHandoffs = handoffs["source"];
        Assert.Single(sourceHandoffs);
        Assert.Equal(customDescription, sourceHandoffs["target"]);
    }

    [Fact]
    public void Add_WithAgentAndTargetName_AddsHandoffWithDescription()
    {
        // Arrange
        OrchestrationHandoffs handoffs = [];

        Agent sourceAgent = CreateAgent("source", "Source Agent");
        string targetName = "targetName";
        string description = "Target description";

        // Act
        handoffs.Add(sourceAgent, targetName, description);

        // Assert
        Assert.Single(handoffs);
        AgentHandoffs sourceHandoffs = handoffs["source"];
        Assert.Single(sourceHandoffs);
        Assert.Equal(description, sourceHandoffs[targetName]);
    }

    [Fact]
    public void Add_WithSourceNameAndTargetName_AddsHandoffWithDescription()
    {
        // Arrange
        OrchestrationHandoffs handoffs = [];

        string sourceName = "sourceName";
        string targetName = "targetName";
        string description = "Target description";

        // Act
        handoffs.Add(sourceName, targetName, description);

        // Assert
        Assert.Single(handoffs);
        AgentHandoffs sourceHandoffs = handoffs[sourceName];
        Assert.Single(sourceHandoffs);
        Assert.Equal(description, sourceHandoffs[targetName]);
    }

    [Fact]
    public void Add_WithMultipleSourcesAndTargets_CreatesCorrectStructure()
    {
        // Arrange
        OrchestrationHandoffs handoffs = [];

        Agent source1 = CreateAgent("source1", "Source Agent 1");
        Agent source2 = CreateAgent("source2", "Source Agent 2");

        Agent target1 = CreateAgent("target1", "Target Agent 1");
        Agent target2 = CreateAgent("target2", "Target Agent 2");
        Agent target3 = CreateAgent("target3", "Target Agent 3");

        // Act
        handoffs.Add(source1, target1, target2);
        handoffs.Add(source2, target2, target3);
        handoffs.Add(source1, target3, "Custom description");

        // Assert
        Assert.Equal(2, handoffs.Count);

        // Check source1's targets
        AgentHandoffs source1Handoffs = handoffs["source1"];
        Assert.Equal(3, source1Handoffs.Count);
        Assert.Equal("Target Agent 1", source1Handoffs["target1"]);
        Assert.Equal("Target Agent 2", source1Handoffs["target2"]);
        Assert.Equal("Custom description", source1Handoffs["target3"]);

        // Check source2's targets
        AgentHandoffs source2Handoffs = handoffs["source2"];
        Assert.Equal(2, source2Handoffs.Count);
        Assert.Equal("Target Agent 2", source2Handoffs["target2"]);
        Assert.Equal("Target Agent 3", source2Handoffs["target3"]);
    }

    [Fact]
    public void StaticAdd_CreatesNewOrchestrationHandoffs()
    {
        // Arrange
        Agent source = CreateAgent("source", "Source Agent");
        Agent target1 = CreateAgent("target1", "Target Agent 1");
        Agent target2 = CreateAgent("target2", "Target Agent 2");

        // Act
        OrchestrationHandoffs handoffs = OrchestrationHandoffs.Add(source, target1, target2);

        // Assert
        Assert.NotNull(handoffs);
        Assert.Single(handoffs);
        Assert.True(handoffs.ContainsKey("source"));

        AgentHandoffs sourceHandoffs = handoffs["source"];
        Assert.Equal(2, sourceHandoffs.Count);
        Assert.Equal("Target Agent 1", sourceHandoffs["target1"]);
        Assert.Equal("Target Agent 2", sourceHandoffs["target2"]);
    }

    [Fact]
    public void Add_WithAgentsWithNoNameUsesId()
    {
        // Arrange
        OrchestrationHandoffs handoffs = [];

        Agent sourceAgent = CreateAgent(id: "source-id", name: null);
        Agent targetAgent = CreateAgent(id: "target-id", name: null, description: "Target Description");

        // Act
        handoffs.Add(sourceAgent, targetAgent);

        // Assert
        Assert.Single(handoffs);
        Assert.True(handoffs.ContainsKey("source-id"));

        AgentHandoffs sourceHandoffs = handoffs["source-id"];
        Assert.Single(sourceHandoffs);
        Assert.Equal("Target Description", sourceHandoffs["target-id"]);
    }

    [Fact]
    public void Add_WithTargetWithNoDescription_UsesEmptyString()
    {
        // Arrange
        OrchestrationHandoffs handoffs = [];

        Agent sourceAgent = CreateAgent("source", "Source Agent");
        Agent targetAgent = CreateAgent("target", null);

        // Act
        handoffs.Add(sourceAgent, targetAgent);

        // Assert
        Assert.Single(handoffs);
        AgentHandoffs sourceHandoffs = handoffs["source"];
        Assert.Single(sourceHandoffs);
        Assert.Equal(string.Empty, sourceHandoffs["target"]);
    }

    private static ChatCompletionAgent CreateAgent(string id, string? description = null, string? name = null)
    {
        ChatCompletionAgent mockAgent =
            new()
            {
                Id = id,
                Description = description,
                Name = name,
            };

        return mockAgent;
    }
}
