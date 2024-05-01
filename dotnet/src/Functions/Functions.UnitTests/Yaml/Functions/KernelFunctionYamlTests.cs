// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.ToolBehaviors;
using Microsoft.SemanticKernel.Connectors.OpenAI;

using Xunit;
using YamlDotNet.Serialization;
using YamlDotNet.Serialization.NamingConventions;

namespace SemanticKernel.Functions.UnitTests.Yaml;

public class KernelFunctionYamlTests
{
    private readonly ISerializer _serializer;

    public KernelFunctionYamlTests()
    {
        this._serializer = new SerializerBuilder()
            .WithNamingConvention(UnderscoredNamingConvention.Instance)
            .Build();
    }

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
            .WithTypeConverter(new PromptExecutionSettingsTypeConverter())
            .Build();
        var promptFunctionModel = deserializer.Deserialize<PromptTemplateConfig>(this._yaml);

        // Act
        var executionSettings = OpenAIPromptExecutionSettings.FromExecutionSettings(promptFunctionModel.ExecutionSettings["service1"]);

        // Assert
        Assert.NotNull(executionSettings);
        Assert.Equal("gpt-4", executionSettings.ModelId);
        Assert.Equal(1.0, executionSettings.Temperature);
        Assert.Equal(0.0, executionSettings.TopP);
    }

    [Fact]
    public void ItShouldDeserializeFunctionCallChoices()
    {
        // Act
        var promptTemplateConfig = KernelFunctionYaml.ToPromptTemplateConfig(this._yaml);

        // Assert
        Assert.NotNull(promptTemplateConfig?.ExecutionSettings);
        Assert.Equal(2, promptTemplateConfig.ExecutionSettings.Count);

        // Service with auto function call choice
        var service1ExecutionSettings = promptTemplateConfig.ExecutionSettings["service1"];
        Assert.NotNull(service1ExecutionSettings?.ToolBehaviors);
        Assert.Single(service1ExecutionSettings.ToolBehaviors);

        var service1FunctionCallBehavior = service1ExecutionSettings.ToolBehaviors.Single() as FunctionCallBehavior;
        Assert.NotNull(service1FunctionCallBehavior?.Choice);

        var autoFunctionCallChoice = service1FunctionCallBehavior.Choice as AutoFunctionCallChoice;
        Assert.NotNull(autoFunctionCallChoice?.Functions);
        Assert.Equal("p1.f1", autoFunctionCallChoice.Functions.Single());

        // Service with required function call choice
        var service2ExecutionSettings = promptTemplateConfig.ExecutionSettings["service2"];
        Assert.NotNull(service2ExecutionSettings?.ToolBehaviors);
        Assert.Single(service2ExecutionSettings.ToolBehaviors);

        var service2FunctionCallBehavior = service2ExecutionSettings.ToolBehaviors.Single() as FunctionCallBehavior;
        Assert.NotNull(service2FunctionCallBehavior?.Choice);

        var requiredFunctionCallChoice = service2FunctionCallBehavior.Choice as RequiredFunctionCallChoice;
        Assert.NotNull(requiredFunctionCallChoice?.Functions);
        Assert.Equal("p2.f2", requiredFunctionCallChoice.Functions.Single());
    }

    [Fact]
    public void ItShouldCreateFunctionWithDefaultValueOfStringType()
    {
        // Act
        var function = KernelFunctionYaml.FromPromptYaml(this._yamlWithCustomSettings);

        // Assert
        Assert.NotNull(function?.Metadata?.Parameters);
        Assert.Equal("John", function?.Metadata?.Parameters[0].DefaultValue);
        Assert.Equal("English", function?.Metadata?.Parameters[1].DefaultValue);
    }

    [Fact]
    // This test checks that the logic of imposing a temporary limitation on the default value being a string is in place and works as expected.
    public void ItShouldThrowExceptionWhileCreatingFunctionWithDefaultValueOtherThanString()
    {
        string CreateYaml(object defaultValue)
        {
            var obj = new
            {
                description = "function description",
                input_variables = new[]
                {
                    new
                    {
                        name = "name",
                        description = "description",
                        @default = defaultValue,
                        isRequired = true
                    }
                }
            };

            return this._serializer.Serialize(obj);
        }

        // Act
        Assert.Throws<NotSupportedException>(() => KernelFunctionYaml.FromPromptYaml(CreateYaml(new { p1 = "v1" })));
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

    private readonly string _yaml = """
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
          service1:
            model_id:          gpt-4
            temperature:       1.0
            top_p:             0.0
            presence_penalty:  0.0
            frequency_penalty: 0.0
            max_tokens:        256
            stop_sequences:    []
            tool_behaviors:
              - !function_call_behavior
                choice: !auto
                  functions:
                    - p1.f1
          service2:
            model_id:          gpt-3.5
            temperature:       1.0
            top_p:             0.0
            presence_penalty:  0.0
            frequency_penalty: 0.0
            max_tokens:        256
            stop_sequences:    [ "foo", "bar", "baz" ]
            tool_behaviors:
              - !function_call_behavior
                choice: !required
                  functions:
                    - p2.f2
        """;

    private readonly string _yamlWithCustomSettings = """
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
            default:       English
        execution_settings:
          service1:
            model_id:          gpt-4
            temperature:       1.0
            top_p:             0.0
            presence_penalty:  0.0
            frequency_penalty: 0.0
            max_tokens:        256
            stop_sequences:    []
          service2:
            model_id:          random-model
            temperaturex:      1.0
            top_q:             0.0
            rando_penalty:     0.0
            max_token_count:   256
            stop_sequences:    [ "foo", "bar", "baz" ]
        """;
}
