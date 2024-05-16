// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using Microsoft.SemanticKernel;
using Xunit;
using YamlDotNet.Serialization;
using YamlDotNet.Serialization.NamingConventions;

namespace SemanticKernel.Functions.UnitTests.Yaml;

/// <summary>
/// Tests for <see cref="PromptExecutionSettingsTypeConverter"/>.
/// </summary>
public sealed class PromptExecutionSettingsTypeConverterTests
{
    [Fact]
    public void ItShouldCreatePromptFunctionFromYamlWithCustomModelSettings()
    {
        // Arrange
        var deserializer = new DeserializerBuilder()
            .WithNamingConvention(UnderscoredNamingConvention.Instance)
            .WithTypeConverter(new PromptExecutionSettingsTypeConverter())
            .Build();

        // Act
        var semanticFunctionConfig = deserializer.Deserialize<PromptTemplateConfig>(this._yaml);

        // Assert
        Assert.NotNull(semanticFunctionConfig);
        Assert.Equal("SayHello", semanticFunctionConfig.Name);
        Assert.Equal("Say hello to the specified person using the specified language", semanticFunctionConfig.Description);
        Assert.Equal(2, semanticFunctionConfig.InputVariables.Count);
        Assert.Equal("language", semanticFunctionConfig.InputVariables[1].Name);
        Assert.Equal(3, semanticFunctionConfig.ExecutionSettings.Count);
        Assert.Equal("gpt-4", semanticFunctionConfig.ExecutionSettings["service1"].ModelId);
        Assert.Equal("gpt-3.5", semanticFunctionConfig.ExecutionSettings["service2"].ModelId);
        Assert.Equal("gpt-3.5-turbo", semanticFunctionConfig.ExecutionSettings["service3"].ModelId);
    }

    [Fact]
    public void ItShouldDeserializeFunctionChoiceBehaviors()
    {
        // Act
        var promptTemplateConfig = KernelFunctionYaml.ToPromptTemplateConfig(this._yaml);

        // Assert
        Assert.NotNull(promptTemplateConfig?.ExecutionSettings);
        Assert.Equal(3, promptTemplateConfig.ExecutionSettings.Count);

        // Service with auto function choice behavior
        var service1ExecutionSettings = promptTemplateConfig.ExecutionSettings["service1"];

        var autoFunctionChoiceBehavior = service1ExecutionSettings.FunctionChoiceBehavior as AutoFunctionChoiceBehavior;
        Assert.NotNull(autoFunctionChoiceBehavior?.Functions);
        Assert.Equal("p1-f1", autoFunctionChoiceBehavior.Functions.Single());

        // Service with required function choice behavior
        var service2ExecutionSettings = promptTemplateConfig.ExecutionSettings["service2"];

        var requiredFunctionChoiceBehavior = service2ExecutionSettings.FunctionChoiceBehavior as RequiredFunctionChoiceBehavior;
        Assert.NotNull(requiredFunctionChoiceBehavior?.Functions);
        Assert.Equal("p2-f2", requiredFunctionChoiceBehavior.Functions.Single());

        // Service with none function choice behavior
        var service3ExecutionSettings = promptTemplateConfig.ExecutionSettings["service3"];

        var noneFunctionChoiceBehavior = service3ExecutionSettings.FunctionChoiceBehavior as NoneFunctionChoiceBehavior;
        Assert.NotNull(noneFunctionChoiceBehavior);
        Assert.NotNull(noneFunctionChoiceBehavior?.Functions);
        Assert.Equal("p3-f3", noneFunctionChoiceBehavior.Functions.Single());
    }

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
            function_choice_behavior:
              type: auto
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
            function_choice_behavior:
              type: required
              functions:
              - p2.f2
          service3:
            model_id:          gpt-3.5-turbo
            temperature:       1.0
            top_p:             0.0
            presence_penalty:  0.0
            frequency_penalty: 0.0
            max_tokens:        256
            stop_sequences:    [ "foo", "bar", "baz" ]
            function_choice_behavior:
              type: none
              functions:
              - p3.f3
        """;
}
