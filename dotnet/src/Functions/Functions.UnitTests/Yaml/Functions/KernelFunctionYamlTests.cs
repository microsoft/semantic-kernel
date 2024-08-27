// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using Microsoft.SemanticKernel;
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
    public void ItShouldDeserializeFunctionChoiceBehaviors()
    {
        // Arrange & Act
        var kernel = new Kernel();
        kernel.Plugins.AddFromFunctions("p1", [KernelFunctionFactory.CreateFromMethod(() => { }, "f1")]);
        kernel.Plugins.AddFromFunctions("p2", [KernelFunctionFactory.CreateFromMethod(() => { }, "f2")]);
        kernel.Plugins.AddFromFunctions("p3", [KernelFunctionFactory.CreateFromMethod(() => { }, "f3")]);

        var promptTemplateConfig = KernelFunctionYaml.ToPromptTemplateConfig(this._yaml);

        // Assert
        Assert.NotNull(promptTemplateConfig?.ExecutionSettings);
        Assert.Equal(6, promptTemplateConfig.ExecutionSettings.Count);

        // Service with auto function choice behavior
        var service1ExecutionSettings = promptTemplateConfig.ExecutionSettings["service1"];
        Assert.NotNull(service1ExecutionSettings?.FunctionChoiceBehavior);

        var autoConfig = service1ExecutionSettings.FunctionChoiceBehavior.GetConfiguration(new FunctionChoiceBehaviorConfigurationContext([]) { Kernel = kernel });
        Assert.NotNull(autoConfig);
        Assert.Equal(FunctionChoice.Auto, autoConfig.Choice);
        Assert.NotNull(autoConfig.Functions);
        Assert.Equal("p1", autoConfig.Functions.Single().PluginName);
        Assert.Equal("f1", autoConfig.Functions.Single().Name);

        // Service with required function choice behavior
        var service2ExecutionSettings = promptTemplateConfig.ExecutionSettings["service2"];
        Assert.NotNull(service2ExecutionSettings?.FunctionChoiceBehavior);

        var requiredConfig = service2ExecutionSettings.FunctionChoiceBehavior.GetConfiguration(new FunctionChoiceBehaviorConfigurationContext([]) { Kernel = kernel });
        Assert.NotNull(requiredConfig);
        Assert.Equal(FunctionChoice.Required, requiredConfig.Choice);
        Assert.NotNull(requiredConfig.Functions);
        Assert.Equal("p2", requiredConfig.Functions.Single().PluginName);
        Assert.Equal("f2", requiredConfig.Functions.Single().Name);

        // Service with none function choice behavior
        var service3ExecutionSettings = promptTemplateConfig.ExecutionSettings["service3"];
        Assert.NotNull(service3ExecutionSettings?.FunctionChoiceBehavior);

        var noneConfig = service3ExecutionSettings.FunctionChoiceBehavior.GetConfiguration(new FunctionChoiceBehaviorConfigurationContext([]) { Kernel = kernel });
        Assert.NotNull(noneConfig);
        Assert.Equal(FunctionChoice.None, noneConfig.Choice);
        Assert.NotNull(noneConfig.Functions);
        Assert.Equal("p3", noneConfig.Functions.Single().PluginName);
        Assert.Equal("f3", noneConfig.Functions.Single().Name);

        // AutoFunctionCallChoice with empty functions collection for service4
        var service4ExecutionSettings = promptTemplateConfig.ExecutionSettings["service4"];
        Assert.NotNull(service4ExecutionSettings?.FunctionChoiceBehavior);

        var autoWithEmptyFunctionsConfig = service4ExecutionSettings.FunctionChoiceBehavior.GetConfiguration(new FunctionChoiceBehaviorConfigurationContext(chatHistory: []) { Kernel = kernel });
        Assert.NotNull(autoWithEmptyFunctionsConfig);
        Assert.Equal(FunctionChoice.Auto, autoWithEmptyFunctionsConfig.Choice);
        Assert.Null(autoWithEmptyFunctionsConfig.Functions);

        // AutoFunctionCallChoice with no functions collection for service5
        var service5ExecutionSettings = promptTemplateConfig.ExecutionSettings["service5"];
        Assert.NotNull(service5ExecutionSettings?.FunctionChoiceBehavior);

        var autoWithNoFunctionsConfig = service5ExecutionSettings.FunctionChoiceBehavior.GetConfiguration(new FunctionChoiceBehaviorConfigurationContext(chatHistory: []) { Kernel = kernel });
        Assert.NotNull(autoWithNoFunctionsConfig);
        Assert.Equal(FunctionChoice.Auto, autoWithNoFunctionsConfig.Choice);
        Assert.NotNull(autoWithNoFunctionsConfig.Functions);
        Assert.Equal(3, autoWithNoFunctionsConfig.Functions.Count);
        Assert.Contains(autoWithNoFunctionsConfig.Functions, f => f.PluginName == "p1" && f.Name == "f1");
        Assert.Contains(autoWithNoFunctionsConfig.Functions, f => f.PluginName == "p2" && f.Name == "f2");
        Assert.Contains(autoWithNoFunctionsConfig.Functions, f => f.PluginName == "p3" && f.Name == "f3");

        // No function choice behavior for service6
        var service6ExecutionSettings = promptTemplateConfig.ExecutionSettings["service6"];
        Assert.Null(service6ExecutionSettings?.FunctionChoiceBehavior);
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
            model_id:          gpt-3.5
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
          service4:
            model_id:          gpt-4
            temperature:       1.0
            function_choice_behavior:
              type: auto
              functions: []
          service5:
            model_id:          gpt-4
            temperature:       1.0
            function_choice_behavior:
              type: auto
          service6:
            model_id:          gpt-4
            temperature:       1.0
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
