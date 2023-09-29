// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Linq;
using Microsoft.SemanticKernel.Experimental.Orchestration;
using Xunit;

namespace SemanticKernel.Extensions.UnitTests.Orchestration.FlowOrchestrator;

public class FlowSerializerTests
{
    [Fact]
    public void CanDeserializeFromYaml()
    {
        // Arrange
        var yamlFile = "./Orchestration/FlowOrchestrator/TestData/Flow/flow.yml";
        var content = File.ReadAllText(yamlFile);

        // Act
        var flow = FlowSerializer.DeserializeFromYaml(content);

        // Assert
        this.ValidateFlow(flow);
    }

    [Fact]
    public void CanDeserializeFromJson()
    {
        // Arrange
        var jsonFile = "./Orchestration/FlowOrchestrator/TestData/Flow/flow.json";
        var content = File.ReadAllText(jsonFile);

        // Act
        var flow = FlowSerializer.DeserializeFromJson(content);

        // Assert
        this.ValidateFlow(flow);
    }

    private void ValidateFlow(Flow? flow)
    {
        Assert.NotNull(flow);
        Assert.NotEmpty(flow.Steps);
        Assert.False(string.IsNullOrEmpty(flow.Goal));
        Assert.Contains("breakfast", flow.Provides);
        Assert.Equal(5, flow.Steps.Count);

        var makeCoffeeStep = flow.Steps.First(step => step.Goal == "Make coffee");
        Assert.Equal("coffee_bean", makeCoffeeStep.Requires.Single());
        Assert.Equal("coffee", makeCoffeeStep.Provides.Single());
        Assert.NotNull(makeCoffeeStep.Plugins);
        Assert.Single(makeCoffeeStep.Plugins);
        Assert.Equal(CompletionType.Once, makeCoffeeStep.CompletionType);

        var recipeStep = flow.Steps.First(step => step.Goal == "Recipe");
        Assert.Equal("ingredients", recipeStep.Provides.Single());
        Assert.Equal(CompletionType.AtLeastOnce, recipeStep.CompletionType);

        var lunchStep = flow.Steps.First(step => step is ReferenceFlowStep) as ReferenceFlowStep;
        Assert.NotNull(lunchStep);
        Assert.Equal(CompletionType.Optional, lunchStep.CompletionType);
        Assert.Equal("lunch_flow", lunchStep.FlowName);
    }
}
