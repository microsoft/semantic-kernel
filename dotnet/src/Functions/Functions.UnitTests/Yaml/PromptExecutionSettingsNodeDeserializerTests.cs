// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Xunit;
using YamlDotNet.Serialization;
using YamlDotNet.Serialization.NamingConventions;

namespace SemanticKernel.Functions.UnitTests.Yaml;

/// <summary>
/// Tests for <see cref="PromptExecutionSettingsNodeDeserializer"/>.
/// </summary>
public sealed class PromptExecutionSettingsNodeDeserializerTests
{
    [Fact]
    public void ItShouldCreatePromptFunctionFromYamlWithCustomModelSettings()
    {
        // Arrange
        var deserializer = new DeserializerBuilder()
            .WithNamingConvention(UnderscoredNamingConvention.Instance)
            .WithNodeDeserializer(new PromptExecutionSettingsNodeDeserializer())
            .Build();

        // Act
        var semanticFunctionConfig = deserializer.Deserialize<PromptTemplateConfig>(this._yaml);

        // Assert
        Assert.NotNull(semanticFunctionConfig);
        Assert.Equal("SayHello", semanticFunctionConfig.Name);
        Assert.Equal("Say hello to the specified person using the specified language", semanticFunctionConfig.Description);
        Assert.Equal(2, semanticFunctionConfig.InputVariables.Count);
        Assert.Equal("language", semanticFunctionConfig.InputVariables[1].Name);
        Assert.Equal(2, semanticFunctionConfig.ExecutionSettings.Count);
        Assert.Equal("gpt-4", semanticFunctionConfig.ExecutionSettings["service1"].ModelId);
        Assert.Equal("gpt-3.5", semanticFunctionConfig.ExecutionSettings["service2"].ModelId);
    }

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
        model_id:          gpt-3.5
        temperature:       1.0
        top_p:             0.0
        presence_penalty:  0.0
        frequency_penalty: 0.0
        max_tokens:        256
        stop_sequences:    [ ""foo"", ""bar"", ""baz"" ]
";
}
