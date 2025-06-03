// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Linq;
using Xunit;

namespace Microsoft.SemanticKernel.Functions.UnitTests;

public sealed class PromptYamlKernelExtensionsTests : IDisposable
{
    private readonly IKernelBuilder _kernelBuilder;
    private readonly Kernel _kernel;

    private readonly string _pluginsDirectory;

    private readonly string _plugin1Name;
    private readonly string _plugin2Name;

    public PromptYamlKernelExtensionsTests()
    {
        this._kernelBuilder = Kernel.CreateBuilder();
        this._kernel = this._kernelBuilder.Build();

        this._pluginsDirectory = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString());

        this._plugin1Name = "Plugin1";
        this._plugin2Name = "Plugin2";
        string plugin1Directory = Path.Combine(this._pluginsDirectory, this._plugin1Name);
        string plugin2Directory = Path.Combine(this._pluginsDirectory, this._plugin2Name);

        try
        {
            Directory.CreateDirectory(this._pluginsDirectory);
            Directory.CreateDirectory(plugin1Directory);
            Directory.CreateDirectory(plugin2Directory);

            string yamlFile1Path = Path.Combine(plugin1Directory, $"{nameof(YAML)}.yaml");
            string yamlFile2Path = Path.Combine(plugin1Directory, $"{nameof(YAMLWithCustomSettings)}.yaml");
            string yamlFile3Path = Path.Combine(plugin2Directory, $"{nameof(YAMLNoExecutionSettings)}.yaml");

            File.WriteAllText(yamlFile1Path, YAML);
            File.WriteAllText(yamlFile2Path, YAMLWithCustomSettings);
            File.WriteAllText(yamlFile3Path, YAMLNoExecutionSettings);

            // Add .yml file to plugin2 to ensure both extensions are supported
            string ymlFile1Path = Path.Combine(plugin2Directory, $"{nameof(YAML)}.yml");

            File.WriteAllText(ymlFile1Path, YAML);
        }
        catch (Exception)
        {
            Directory.Delete(this._pluginsDirectory, true);
            throw;
        }
    }

    public void Dispose()
    {
        if (Directory.Exists(this._pluginsDirectory))
        {
            Directory.Delete(this._pluginsDirectory, true);
        }
    }

    [Fact]
    public void ItShouldCreatePluginFromPromptDirectoryYaml()
    {
        // Arrange
        // Act
        var plugins = Directory
            .EnumerateDirectories(this._pluginsDirectory)
            .Select(directory => this._kernel.CreatePluginFromPromptDirectoryYaml(directory));

        this._kernel.Plugins.AddRange(plugins);

        // Assert
        VerifyPluginCounts(this._kernel, this._plugin1Name, this._plugin2Name);
    }

    [Fact]
    public void ItShouldImportPluginFromPromptDirectoryYaml()
    {
        // Arrange
        // Act
        foreach (string directory in Directory.EnumerateDirectories(this._pluginsDirectory))
        {
            this._kernel.ImportPluginFromPromptDirectoryYaml(directory);
        }

        // Assert
        VerifyPluginCounts(this._kernel, this._plugin1Name, this._plugin2Name);
    }

    [Fact]
    public void ItShouldAddFromPromptDirectoryYaml()
    {
        // Arrange
        // Act
        foreach (string directory in Directory.EnumerateDirectories(this._pluginsDirectory))
        {
            this._kernelBuilder.Plugins.AddFromPromptDirectoryYaml(directory);
        }

        var kernel = this._kernelBuilder.Build();

        // Assert
        VerifyPluginCounts(kernel, this._plugin1Name, this._plugin2Name);
    }

    private static void VerifyPluginCounts(Kernel kernel, string expectedPlugin1, string expectedPlugin2)
    {
        Assert.NotNull(kernel.Plugins);
        Assert.Equal(2, kernel.Plugins.Count);

        Assert.NotNull(kernel.Plugins[expectedPlugin1]);
        Assert.NotNull(kernel.Plugins[expectedPlugin2]);

        Assert.Equal(2, kernel.Plugins[expectedPlugin1].Count());
        Assert.Equal(2, kernel.Plugins[expectedPlugin2].Count());
    }

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
                                                  name:            SayHelloWithCustomSettings
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

    private const string YAMLNoExecutionSettings = """
                                                   template_format: semantic-kernel
                                                   template:        Say hello world to {{$name}} in {{$language}}
                                                   description:     Say hello to the specified person using the specified language
                                                   name:            SayHelloNoExecutionSettings
                                                   input_variables:
                                                     - name:          name
                                                       description:   The name of the person to greet
                                                       default:       John
                                                     - name:          language
                                                       description:   The language to generate the greeting in
                                                       default: English
                                                   """;
}
