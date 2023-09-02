// Copyright (c) Microsoft. All rights reserved.
namespace SemanticKernel.UnitTests.AI.FunctionCalling;

using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.FunctionCalling.Extensions;
using Microsoft.SemanticKernel.SkillDefinition;
using Xunit;


public class FunctionExtensionTests
{
    [Fact]
    public void ToFunctionDefinition_ShouldConvert_FunctionViewToFunctionDefinition()
    {
        // Arrange
        var functionView = new FunctionView(
            "testFunction",
            "testSkill",
            "testDescription",
            new List<ParameterView>
            {
                new("param1", "description1", "default1", ParameterViewType.String),
                new("param2", "description2", "default2", ParameterViewType.Number)
            },
            true,
            true);

        // Act
        var result = functionView.ToFunctionDefinition();

        // Assert
        Assert.Equal($"{functionView.SkillName}.{functionView.Name}", result.Name);
        Assert.Equal(functionView.Description, result.Description);

        var parametersJson = result.Parameters.ToString();
        using var parametersDoc = JsonDocument.Parse(parametersJson);
        Dictionary<string, JsonElement> propertiesDict = parametersDoc.RootElement.GetProperty("properties").EnumerateObject().ToDictionary(item => item.Name, item => item.Value);

        Assert.True(propertiesDict.ContainsKey(functionView.Parameters[0].Name));

        if (propertiesDict.ContainsKey(functionView.Parameters[0].Name))
        {
            Assert.Equal(functionView.Parameters[0].Description, propertiesDict[functionView.Parameters[0].Name].GetProperty("description").GetString());
            Assert.Equal(functionView.Parameters[0].DefaultValue, propertiesDict[functionView.Parameters[0].Name].GetProperty("defaultValue").GetString());
            Assert.Equal(functionView.Parameters[0].Type?.Name, propertiesDict[functionView.Parameters[0].Name].GetProperty("type").GetString());
        }

        Assert.True(propertiesDict.ContainsKey(functionView.Parameters[1].Name));

        if (propertiesDict.ContainsKey(functionView.Parameters[1].Name))
        {
            Assert.Equal(functionView.Parameters[1].Description, propertiesDict[functionView.Parameters[1].Name].GetProperty("description").GetString());
            Assert.Equal(functionView.Parameters[1].DefaultValue, propertiesDict[functionView.Parameters[1].Name].GetProperty("defaultValue").GetString());
            Assert.Equal(functionView.Parameters[1].Type?.Name, propertiesDict[functionView.Parameters[1].Name].GetProperty("type").GetString());
        }
    }
}
