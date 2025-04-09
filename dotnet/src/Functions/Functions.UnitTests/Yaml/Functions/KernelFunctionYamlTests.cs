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
    private readonly Kernel _kernel;

    public KernelFunctionYamlTests()
    {
        this._kernel = new Kernel();
        this._kernel.Plugins.AddFromFunctions("p1", [KernelFunctionFactory.CreateFromMethod(() => { }, "f1")]);
        this._kernel.Plugins.AddFromFunctions("p2", [KernelFunctionFactory.CreateFromMethod(() => { }, "f2")]);
        this._kernel.Plugins.AddFromFunctions("p3", [KernelFunctionFactory.CreateFromMethod(() => { }, "f3")]);

        this._serializer = new SerializerBuilder()
            .WithNamingConvention(UnderscoredNamingConvention.Instance)
            .Build();
    }

    [Fact]
    public void ItShouldCreateFunctionFromPromptYamlWithNoExecutionSettings()
    {
        // Arrange
        // Act
        var function = KernelFunctionYaml.FromPromptYaml(YAMLNoExecutionSettings);

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
        var function = KernelFunctionYaml.FromPromptYaml(YAML);

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
        var function = KernelFunctionYaml.FromPromptYaml(YAMLWithCustomSettings);

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
        var promptFunctionModel = deserializer.Deserialize<PromptTemplateConfig>(YAML);

        // Act
        var executionSettings = OpenAIPromptExecutionSettings.FromExecutionSettings(promptFunctionModel.ExecutionSettings["service1"]);

        // Assert
        Assert.NotNull(executionSettings);
        Assert.Equal("gpt-4", executionSettings.ModelId);
        Assert.Equal(1.0, executionSettings.Temperature);
        Assert.Equal(0.0, executionSettings.TopP);
    }

    [Fact]
    public void ItShouldDeserializeAutoFunctionChoiceBehaviors()
    {
        // Act
        var promptTemplateConfig = KernelFunctionYaml.ToPromptTemplateConfig(YAML);

        // Assert
        Assert.NotNull(promptTemplateConfig?.ExecutionSettings);

        // Service with auto function choice behavior
        var executionSettings = promptTemplateConfig.ExecutionSettings["service1"];
        Assert.NotNull(executionSettings?.FunctionChoiceBehavior);

        var config = executionSettings.FunctionChoiceBehavior.GetConfiguration(new FunctionChoiceBehaviorConfigurationContext([]) { Kernel = this._kernel });
        Assert.NotNull(config);
        Assert.Equal(FunctionChoice.Auto, config.Choice);
        Assert.NotNull(config.Functions);
        Assert.Equal("p1", config.Functions.Single().PluginName);
        Assert.Equal("f1", config.Functions.Single().Name);
    }

    [Fact]
    public void ItShouldDeserializeRequiredFunctionChoiceBehaviors()
    {
        // Act
        var promptTemplateConfig = KernelFunctionYaml.ToPromptTemplateConfig(YAML);

        // Assert
        Assert.NotNull(promptTemplateConfig?.ExecutionSettings);

        // Service with required function choice behavior
        var executionSettings = promptTemplateConfig.ExecutionSettings["service2"];
        Assert.NotNull(executionSettings?.FunctionChoiceBehavior);

        var config = executionSettings.FunctionChoiceBehavior.GetConfiguration(new FunctionChoiceBehaviorConfigurationContext([]) { Kernel = this._kernel });
        Assert.NotNull(config);
        Assert.Equal(FunctionChoice.Required, config.Choice);
        Assert.NotNull(config.Functions);
        Assert.Equal("p2", config.Functions.Single().PluginName);
        Assert.Equal("f2", config.Functions.Single().Name);
    }

    [Fact]
    public void ItShouldDeserializeNoneFunctionChoiceBehaviors()
    {
        // Act
        var promptTemplateConfig = KernelFunctionYaml.ToPromptTemplateConfig(YAML);

        // Assert
        Assert.NotNull(promptTemplateConfig?.ExecutionSettings);

        // Service with none function choice behavior
        var executionSettings = promptTemplateConfig.ExecutionSettings["service3"];
        Assert.NotNull(executionSettings?.FunctionChoiceBehavior);

        var noneConfig = executionSettings.FunctionChoiceBehavior.GetConfiguration(new FunctionChoiceBehaviorConfigurationContext([]) { Kernel = this._kernel });
        Assert.NotNull(noneConfig);
        Assert.Equal(FunctionChoice.None, noneConfig.Choice);
        Assert.NotNull(noneConfig.Functions);
        Assert.Equal("p3", noneConfig.Functions.Single().PluginName);
        Assert.Equal("f3", noneConfig.Functions.Single().Name);
    }

    [Fact]
    public void ItShouldCreateFunctionWithDefaultValueOfStringType()
    {
        // Act
        var function = KernelFunctionYaml.FromPromptYaml(YAMLWithCustomSettings);

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

    private const string YAMLNoExecutionSettings = """
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
                                                    """;

    private const string YAML = """
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
                                """;

    private const string YAMLWithCustomSettings = """
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
