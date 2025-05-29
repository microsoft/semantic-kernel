// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

namespace Plugins;

/// <summary>
/// This sample shows how to create templated plugins from file directories.
/// </summary>
public class CreatePromptPluginFromDirectory(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task ImportAndUsePromptPluginFromDirectoryWithOpenAI()
    {
        // Get the current directory of the application
        var pluginDirectory = Path.Combine(AppContext.BaseDirectory, "Plugins", "FunPlugin");

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        CreateFileBasedPluginTemplate(pluginDirectory);

        var funPlugin = kernel.ImportPluginFromPromptDirectoryYaml(pluginDirectory, "FunPlugin");

        // Invoke the plugin with a prompt
        var result = await kernel.InvokeAsync(funPlugin["Joke"], new()
        {
            ["input"] = "Why did the chicken cross the road?",
            ["style"] = "dad joke"
        });

        Console.WriteLine(result);
    }

    /// <summary>
    /// After running this method, a new importable plugin directory structure will be created at the application root.
    /// <code>
    /// ./Plugins/FunPlugin/
    ///    joke.yml
    /// </code>
    /// Within the <c>FunPlugin</c> directory, any yml file will be imported as a distinct prompt function for the <see cref="KernelPlugin"/>.
    /// </summary>
    private static void CreateFileBasedPluginTemplate(string pluginRootDirectory)
    {
        // Create the sub-directory for the plugin function "Joke"
        var pluginRelativeDirectory = Path.Combine(pluginRootDirectory, "Joke");

        const string PluginYmlFileContent =
            """
            name: Joke
            template: |
              WRITE EXACTLY ONE JOKE or HUMOROUS STORY ABOUT THE TOPIC BELOW
            
              JOKE MUST BE:
              - G RATED
              - WORKPLACE/FAMILY SAFE
              NO SEXISM, RACISM OR OTHER BIAS/BIGOTRY
            
              BE CREATIVE AND FUNNY. I WANT TO LAUGH.
              Incorporate the style suggestion, if provided: {{$style}}
              +++++
            
              {{$input}}
              +++++
            template_format: semantic-kernel
            description: A function that generates a story about a topic.
            input_variables:
              - name: input
                description: Joke subject.
                is_required: true
              - name: style
                description: Give a hint about the desired joke style.
                is_required: true
            output_variable:
              description: The generated funny joke.
            execution_settings:
              default:
                temperature: 0.9
                max_tokens: 1000
                top_p: 0.0
                presence_penalty: 0.0
                frequency_penalty: 0.0
            """;

        // Create the directory structure
        if (!Directory.Exists(pluginRootDirectory))
        {
            Directory.CreateDirectory(pluginRootDirectory);
        }

        // Create the config.json file if not exists
        var ymlFilePath = Path.Combine(pluginRootDirectory, "joke.yml");
        File.WriteAllText(ymlFilePath, PluginYmlFileContent);
    }
}
