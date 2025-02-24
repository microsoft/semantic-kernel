// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.ComponentModel;
using Amazon.BedrockAgentRuntime.Model;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.Bedrock.Extensions;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Bedrock.Extensions;

/// <summary>
/// Unit testing of <see cref="BedrockFunctionSchemaExtensions"/>.
/// </summary>
public class BedrockFunctionSchemaExtensionsTests
{
    /// <summary>
    /// Verify the conversion of a <see cref="FunctionParameter"/> to a <see cref="KernelArguments"/>.
    /// </summary>
    [Fact]
    public void VerifyFromFunctionParameters()
    {
        // Arrange
        List<FunctionParameter> parameters =
        [
            new FunctionParameter()
            {
                Name = "TestParameter",
                Type = Amazon.BedrockAgent.Type.String,
            },
        ];

        // Act
        KernelArguments arguments = parameters.FromFunctionParameters(null);

        // Assert
        Assert.Single(arguments);
        Assert.True(arguments.ContainsName("TestParameter"));
    }

    /// <summary>
    /// Verify the conversion of a <see cref="FunctionParameter"/> to a <see cref="KernelArguments"/> with existing arguments.
    /// </summary>
    [Fact]
    public void VerifyFromFunctionParametersWithArguments()
    {
        // Arrange
        List<FunctionParameter> parameters =
        [
            new FunctionParameter()
            {
                Name = "TestParameter",
                Type = Amazon.BedrockAgent.Type.String,
            },
        ];

        KernelArguments arguments = new()
        {
            { "ExistingParameter", "ExistingValue" }
        };

        // Act
        KernelArguments updatedArguments = parameters.FromFunctionParameters(arguments);

        // Assert
        Assert.Equal(2, updatedArguments.Count);
        Assert.True(updatedArguments.ContainsName("TestParameter"));
        Assert.True(updatedArguments.ContainsName("ExistingParameter"));
    }

    /// <summary>
    /// Verify the conversion of a <see cref="Kernel"/> plugin to a <see cref="Amazon.BedrockAgent.Model.FunctionSchema"/>.
    /// </summary>
    [Fact]
    public void VerifyToFunctionSchema()
    {
        // Arrange
        (Kernel kernel, KernelFunction function, KernelParameterMetadata parameter) = this.CreateKernelPlugin();

        // Act
        Amazon.BedrockAgent.Model.FunctionSchema schema = kernel.ToFunctionSchema();

        // Assert
        Assert.Single(schema.Functions);
        Assert.Equal(function.Name, schema.Functions[0].Name);
        Assert.Equal(function.Description, schema.Functions[0].Description);
        Assert.True(schema.Functions[0].Parameters.ContainsKey(parameter.Name));
        Assert.Equal(parameter.Description, schema.Functions[0].Parameters[parameter.Name].Description);
        Assert.True(schema.Functions[0].Parameters[parameter.Name].Required);
        Assert.Equal(Amazon.BedrockAgent.Type.String, schema.Functions[0].Parameters[parameter.Name].Type);
        Assert.Equal(Amazon.BedrockAgent.RequireConfirmation.DISABLED, schema.Functions[0].RequireConfirmation);
    }

    private (Kernel, KernelFunction, KernelParameterMetadata) CreateKernelPlugin()
    {
        Kernel kernel = new();
        kernel.Plugins.Add(KernelPluginFactory.CreateFromType<WeatherPlugin>());
        var function = kernel.Plugins["WeatherPlugin"]["Current"];
        var parameter = function.Metadata.Parameters[0];
        return (kernel, function, parameter);
    }

    private sealed class WeatherPlugin
    {
        [KernelFunction, Description("Provides realtime weather information.")]
        public string Current([Description("The location to get the weather for.")] string location)
        {
            return $"The current weather in {location} is 72 degrees.";
        }
    }
}
