// Copyright (c) Microsoft. All rights reserved.

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
    private readonly IDeserializer _deserializer;

    private readonly Kernel _kernel;

    public PromptExecutionSettingsTypeConverterTests()
    {
        this._deserializer = new DeserializerBuilder()
            .WithNamingConvention(UnderscoredNamingConvention.Instance)
            .WithTypeConverter(new PromptExecutionSettingsTypeConverter())
        .Build();

        this._kernel = new Kernel();
        this._kernel.Plugins.Add(GetTestPlugin());
    }

    [Fact]
    public void ItShouldCreatePromptFunctionFromYamlWithCustomModelSettings()
    {
        // Act
        var semanticFunctionConfig = this._deserializer.Deserialize<PromptTemplateConfig>(this._yaml);

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
    public void ItShouldDeserializeAutoFunctionChoiceBehaviorFromYamlWithNoFunctionsProperty()
    {
        // Arrange
        var yaml = """
            function_choice_behavior:
              type: auto
        """;

        var executionSettings = this._deserializer.Deserialize<PromptExecutionSettings>(yaml);

        // Act
        var config = executionSettings!.FunctionChoiceBehavior!.GetConfiguration(new(chatHistory: []) { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);

        Assert.Equal(FunctionChoice.Auto, config.Choice);

        Assert.True(config.AutoInvoke);

        Assert.NotNull(config?.Functions);
        Assert.Equal(3, config.Functions.Count);
        Assert.Contains(config.Functions, f => f.PluginName == "MyPlugin" && f.Name == "Function1");
        Assert.Contains(config.Functions, f => f.PluginName == "MyPlugin" && f.Name == "Function2");
        Assert.Contains(config.Functions, f => f.PluginName == "MyPlugin" && f.Name == "Function3");
    }

    [Fact]
    public void ItShouldDeserializeAutoFunctionChoiceBehaviorFromYamlWithEmptyFunctionsProperty()
    {
        // Arrange
        var yaml = """
            function_choice_behavior:
              type: auto
              functions: []
        """;

        var executionSettings = this._deserializer.Deserialize<PromptExecutionSettings>(yaml);

        // Act
        var config = executionSettings!.FunctionChoiceBehavior!.GetConfiguration(new(chatHistory: []) { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);

        Assert.Equal(FunctionChoice.Auto, config.Choice);

        Assert.True(config.AutoInvoke);

        Assert.Null(config?.Functions);
    }

    [Fact]
    public void ItShouldDeserializeAutoFunctionChoiceBehaviorFromYamlWithSpecifiedFunctionsProperty()
    {
        // Arrange
        var yaml = """
            function_choice_behavior:
              type: auto
              functions:
              - MyPlugin.Function1
              - MyPlugin.Function3
        """;

        var executionSettings = this._deserializer.Deserialize<PromptExecutionSettings>(yaml);

        // Act
        var config = executionSettings!.FunctionChoiceBehavior!.GetConfiguration(new(chatHistory: []) { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);

        Assert.Equal(FunctionChoice.Auto, config.Choice);

        Assert.True(config.AutoInvoke);

        Assert.NotNull(config?.Functions);
        Assert.Equal(2, config.Functions.Count);
        Assert.Contains(config.Functions, f => f.PluginName == "MyPlugin" && f.Name == "Function1");
        Assert.Contains(config.Functions, f => f.PluginName == "MyPlugin" && f.Name == "Function3");
    }

    [Fact]
    public void ItShouldDeserializeRequiredFunctionChoiceBehaviorFromYamlWithNoFunctionsProperty()
    {
        // Arrange
        var yaml = """
            function_choice_behavior:
              type: required
        """;

        var executionSettings = this._deserializer.Deserialize<PromptExecutionSettings>(yaml);

        // Act
        var config = executionSettings!.FunctionChoiceBehavior!.GetConfiguration(new(chatHistory: []) { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);

        Assert.Equal(FunctionChoice.Required, config.Choice);

        Assert.True(config.AutoInvoke);

        Assert.NotNull(config?.Functions);
        Assert.Equal(3, config.Functions.Count);
        Assert.Contains(config.Functions, f => f.PluginName == "MyPlugin" && f.Name == "Function1");
        Assert.Contains(config.Functions, f => f.PluginName == "MyPlugin" && f.Name == "Function2");
        Assert.Contains(config.Functions, f => f.PluginName == "MyPlugin" && f.Name == "Function3");
    }

    [Fact]
    public void ItShouldDeserializeRequiredFunctionChoiceBehaviorFromYamlWithEmptyFunctionsProperty()
    {
        // Arrange
        var yaml = """
            function_choice_behavior:
              type: required
              functions: []
        """;

        var executionSettings = this._deserializer.Deserialize<PromptExecutionSettings>(yaml);

        // Act
        var config = executionSettings!.FunctionChoiceBehavior!.GetConfiguration(new(chatHistory: []) { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);

        Assert.Equal(FunctionChoice.Required, config.Choice);

        Assert.True(config.AutoInvoke);

        Assert.Null(config?.Functions);
    }

    [Fact]
    public void ItShouldDeserializeRequiredFunctionChoiceBehaviorFromYamlWithSpecifiedFunctionsProperty()
    {
        // Arrange
        var yaml = """
            function_choice_behavior:
              type: required
              functions:
              - MyPlugin.Function1
              - MyPlugin.Function3
        """;

        var executionSettings = this._deserializer.Deserialize<PromptExecutionSettings>(yaml);

        // Act
        var config = executionSettings!.FunctionChoiceBehavior!.GetConfiguration(new(chatHistory: []) { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);

        Assert.Equal(FunctionChoice.Required, config.Choice);

        Assert.True(config.AutoInvoke);

        Assert.NotNull(config?.Functions);
        Assert.Equal(2, config.Functions.Count);
        Assert.Contains(config.Functions, f => f.PluginName == "MyPlugin" && f.Name == "Function1");
        Assert.Contains(config.Functions, f => f.PluginName == "MyPlugin" && f.Name == "Function3");
    }

    [Fact]
    public void ItShouldDeserializedNoneFunctionChoiceBehaviorFromYamlWithNoFunctionsProperty()
    {
        // Arrange
        var yaml = """
            function_choice_behavior:
              type: none
        """;

        var executionSettings = this._deserializer.Deserialize<PromptExecutionSettings>(yaml);

        // Act
        var config = executionSettings!.FunctionChoiceBehavior!.GetConfiguration(new(chatHistory: []) { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);

        Assert.Equal(FunctionChoice.None, config.Choice);

        Assert.False(config.AutoInvoke);

        Assert.NotNull(config?.Functions);
        Assert.Equal(3, config.Functions.Count);
        Assert.Contains(config.Functions, f => f.PluginName == "MyPlugin" && f.Name == "Function1");
        Assert.Contains(config.Functions, f => f.PluginName == "MyPlugin" && f.Name == "Function2");
        Assert.Contains(config.Functions, f => f.PluginName == "MyPlugin" && f.Name == "Function3");
    }

    [Fact]
    public void ItShouldDeserializedNoneFunctionChoiceBehaviorFromYamlWithEmptyFunctionsProperty()
    {
        // Arrange
        var yaml = """
            function_choice_behavior:
              type: none
              functions: []
        """;

        var executionSettings = this._deserializer.Deserialize<PromptExecutionSettings>(yaml);

        // Act
        var config = executionSettings!.FunctionChoiceBehavior!.GetConfiguration(new(chatHistory: []) { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);

        Assert.Equal(FunctionChoice.None, config.Choice);

        Assert.False(config.AutoInvoke);

        Assert.Null(config?.Functions);
    }

    [Fact]
    public void ItShouldDeserializedNoneFunctionChoiceBehaviorFromYamlWithSpecifiedFunctionsProperty()
    {
        // Arrange
        var yaml = """
            function_choice_behavior:
              type: none
              functions:
              - MyPlugin.Function1
              - MyPlugin.Function3
        """;

        var executionSettings = this._deserializer.Deserialize<PromptExecutionSettings>(yaml);

        // Act
        var config = executionSettings!.FunctionChoiceBehavior!.GetConfiguration(new(chatHistory: []) { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);

        Assert.Equal(FunctionChoice.None, config.Choice);

        Assert.False(config.AutoInvoke);

        Assert.NotNull(config?.Functions);
        Assert.Equal(2, config.Functions.Count);
        Assert.Contains(config.Functions, f => f.PluginName == "MyPlugin" && f.Name == "Function1");
        Assert.Contains(config.Functions, f => f.PluginName == "MyPlugin" && f.Name == "Function3");
    }

    [Fact]
    public void ItShouldDeserializeAutoFunctionChoiceBehaviorFromJsonWithOptions()
    {
        // Arrange
        var yaml = """
            function_choice_behavior:
              type: auto
              options:
                allow_parallel_calls: true
                allow_concurrent_invocation: true
                allow_strict_schema_adherence: true
        """;

        var executionSettings = this._deserializer.Deserialize<PromptExecutionSettings>(yaml);

        // Act
        var config = executionSettings!.FunctionChoiceBehavior!.GetConfiguration(new(chatHistory: []) { Kernel = this._kernel });

        // Assert
        Assert.True(config.Options.AllowParallelCalls);
        Assert.True(config.Options.AllowConcurrentInvocation);
        Assert.True(config.Options.AllowStrictSchemaAdherence);
    }

    [Fact]
    public void ItShouldDeserializeRequiredFunctionChoiceBehaviorFromJsonWithOptions()
    {
        // Arrange
        var yaml = """
            function_choice_behavior:
              type: required
              options:
                allow_parallel_calls: true
                allow_concurrent_invocation: true
                allow_strict_schema_adherence: true
        """;

        var executionSettings = this._deserializer.Deserialize<PromptExecutionSettings>(yaml);

        // Act
        var config = executionSettings!.FunctionChoiceBehavior!.GetConfiguration(new(chatHistory: []) { Kernel = this._kernel });

        // Assert
        Assert.True(config.Options.AllowParallelCalls);
        Assert.True(config.Options.AllowConcurrentInvocation);
        Assert.True(config.Options.AllowStrictSchemaAdherence);
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

    private static KernelPlugin GetTestPlugin()
    {
        var function1 = KernelFunctionFactory.CreateFromMethod(() => { }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod(() => { }, "Function2");
        var function3 = KernelFunctionFactory.CreateFromMethod(() => { }, "Function3");

        return KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2, function3]);
    }
}
