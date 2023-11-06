// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.Yaml.Extensions;

public class KernelSemanticFunctionYamlExtensionTests
{
    [Fact]
    public void ItShouldCreateSemanticFunctionFromYaml()
    {
        // Arrange
        var kernel = new KernelBuilder().Build();

        // Act
        var skfunction = kernel.CreateSemanticFunctionFromYaml(this._yaml);

        // Assert
        Assert.NotNull(skfunction);
    }

    private readonly string _yaml = @"
    template_format: semantic-kernel
    template:        Say hello world to {{$name}} in {{$language}}
    description:     Say hello to the specified person using the specified language
    plugin_name:     DemoPlugin
    name:            SayHello
    input_parameters:
      - name:          name
        description:   The name of the person to greet
        default_value: John
      - name:          language
        description:   The language to generate the greeting in
        default_value: English
    model_settings:
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
        stop_sequences:    []
";
}
