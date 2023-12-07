// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;
using YamlDotNet.Serialization;
using YamlDotNet.Serialization.NamingConventions;

namespace SemanticKernel.Functions.UnitTests.Yaml;

public class KernelFunctionYamlTests
{
    [Fact]
    public void ItShouldCreateFunctionFromPromptYamlWithNoExecutionSettings()
    {
        // Arrange
        // Act
        var function = KernelFunctionYaml.FromPromptYaml(this._yamlNoExecutionSettings);

        // Assert
        Assert.NotNull(function);
        Assert.Equal("SayHello", function.Name);
        Assert.Equal("Say hello to the specified person using the specified language", function.Description);
        Assert.Equal(2, function.Metadata.Parameters.Count);
        //Assert.Equal(0, function.ExecutionSettings.Count);
    }

    [Fact]
    public void ItShouldCreateFunctionFromPromptYaml()
    {
        // Arrange
        // Act
        var function = KernelFunctionYaml.FromPromptYaml(this._yaml);

        // Assert
        Assert.NotNull(function);
        Assert.Equal("SayHello", function.Name);
        Assert.Equal("Say hello to the specified person using the specified language", function.Description);
    }

    [Fact]
    public void ItShouldCreateFunctionFromPromptYamlWithCustomExecutionSettings()
    {
        // Arrange
        // Act
        var function = KernelFunctionYaml.FromPromptYaml(this._yamlWithCustomSettings);

        // Assert
        Assert.NotNull(function);
        Assert.Equal("SayHello", function.Name);
        Assert.Equal("Say hello to the specified person using the specified language", function.Description);
        Assert.Equal(2, function.Metadata.Parameters.Count);
    }

    [Fact]
    public void ItShouldSupportCreatingOpenAIExecutionSettings()
    {
        // Arrange
        var deserializer = new DeserializerBuilder()
            .WithNamingConvention(UnderscoredNamingConvention.Instance)
            .WithNodeDeserializer(new PromptExecutionSettingsNodeDeserializer())
            .Build();
        var promptFunctionModel = deserializer.Deserialize<PromptTemplateConfig>(this._yaml);

        // Act
        var executionSettings = OpenAIPromptExecutionSettings.FromExecutionSettings(promptFunctionModel.ExecutionSettings[0]);

        // Assert
        Assert.NotNull(executionSettings);
        Assert.Equal("gpt-4", executionSettings.ModelId);
        Assert.Equal(1.0, executionSettings.Temperature);
        Assert.Equal(0.0, executionSettings.TopP);
    }

    private readonly string _yamlNoExecutionSettings = @"
    template_format: semantic-kernel
    template:        Say hello world to {{$name}} in {{$language}}
    description:     Say hello to the specified person using the specified language
    name:            SayHello
    input_variables:
      - name:          name
        description:   The name of the person to greet
        default:       John
      - name:          language
        description:   The language to generate the greeting in
        default: English
";

    private readonly string _yaml = @"
    template_format: semantic-kernel
    template:        Say hello world to {{$name}} in {{$language}}
    description:     Say hello to the specified person using the specified language
    name:            SayHello
    input_variables:
      - name:          name
        description:   The name of the person to greet
        default:       John
      - name:          language
        description:   The language to generate the greeting in
        default: English
    execution_settings:
      - model_id:          gpt-4
        temperature:       1.0
        top_p:             0.0
        presence_penalty:  0.0
        frequency_penalty: 0.0
        max_tokens:        256
        stop_sequences:    []
      - model_id:          gpt-3.5
        temperature:       1.0
        top_p:             0.0
        presence_penalty:  0.0
        frequency_penalty: 0.0
        max_tokens:        256
        stop_sequences:    [ ""foo"", ""bar"", ""baz"" ]
";

    private readonly string _yamlWithCustomSettings = @"
    template_format: semantic-kernel
    template:        Say hello world to {{$name}} in {{$language}}
    description:     Say hello to the specified person using the specified language
    name:            SayHello
    input_variables:
      - name:          name
        description:   The name of the person to greet
        default:       John
      - name:          language
        description:   The language to generate the greeting in
        default: English
    execution_settings:
      - model_id:          gpt-4
        temperature:       1.0
        top_p:             0.0
        presence_penalty:  0.0
        frequency_penalty: 0.0
        max_tokens:        256
        stop_sequences:    []
      - model_id:          random-model
        temperaturex:      1.0
        top_q:             0.0
        rando_penalty:     0.0
        max_token_count:   256
        stop_sequences:    [ ""foo"", ""bar"", ""baz"" ]
";
}
