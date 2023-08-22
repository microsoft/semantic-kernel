// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernel.Extensions.UnitTests.Planning.FlowPlanner;

using System.IO;
using System.Linq;
using Microsoft.SemanticKernel.Planning.Flow;
using Xunit;

public class FlowSerializerTests
{
    [Fact]
    public void CanDeserializeFromYaml()
    {
        // Arrange
        var yamlFile = "./Planning/FlowPlanner/TestData/Flow/flow.yml";
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
        var jsonFile = "./Planning/FlowPlanner/TestData/Flow/flow.json";
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
        Assert.Equal("breakfast", flow.Provides.Single());
        Assert.Equal(4, flow.Steps.Count);

        var makeCoffeeStep = flow.Steps.First(step => step.Goal == "Make coffee");
        Assert.Equal("coffee_bean", makeCoffeeStep.Requires.Single());
        Assert.Equal("coffee", makeCoffeeStep.Provides.Single());
        Assert.Equal(CompletionType.Once, makeCoffeeStep.CompletionType);

        var recipeStep = flow.Steps.First(step => step.Goal == "Recipe");
        Assert.Equal("ingredients", recipeStep.Provides.Single());
        Assert.Equal(CompletionType.AtLeastOnce, recipeStep.CompletionType);
    }
}
