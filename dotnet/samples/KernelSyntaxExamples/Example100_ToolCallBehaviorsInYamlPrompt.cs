// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Examples;
using Microsoft.SemanticKernel;
using Xunit;
using Xunit.Abstractions;

namespace GettingStarted;

/// <summary>
/// This example shows how to create a prompt <see cref="KernelFunction"/> from a YAML resource.
/// </summary>
public sealed class Example100_ToolCallBehaviorsInYamlPrompt(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Show how to create a prompt <see cref="KernelFunction"/> from a YAML resource.
    /// </summary>
    [Fact]
    public async Task RunAsync()
    {
        // Create a kernel with OpenAI chat completion
        Kernel kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        // Add a plugin with some helper functions we want to allow the model to utilize.
        kernel.ImportPluginFromFunctions("HelperFunctions",
        [
            kernel.CreateFunctionFromMethod(() => DateTime.UtcNow.ToString("R"), "GetCurrentUtcTime", "Retrieves the current time in UTC."),
            kernel.CreateFunctionFromMethod((string cityName) =>
                cityName switch
                {
                    "Boston" => "61 and rainy",
                    "London" => "55 and cloudy",
                    "Miami" => "80 and sunny",
                    "Paris" => "60 and rainy",
                    "Tokyo" => "50 and sunny",
                    "Sydney" => "75 and sunny",
                    "Tel Aviv" => "80 and sunny",
                    _ => "31 and snowing",
                }, "Get_Weather_For_City", "Gets the current weather for the specified city"),
        ]);

        var generateStoryYaml =
            """
            name: GenerateStory
            template: |
              Given the current time of day and weather, what is the likely color of the sky in Boston?
            template_format: semantic-kernel
            description: A function that returns sky color in a city.
            output_variable:
              description: The sky color.
            execution_settings:
              default:
                temperature: 0.4
                tool_behaviors:
                  - !function_call_behavior
                    choice: !auto
                      functions:
                        - HelperFunctions.Get_Weather_For_City
            """;
        var function = kernel.CreateFunctionFromPromptYaml(generateStoryYaml);

        var result = await kernel.InvokeAsync(function);

        WriteLine(result);
    }
}
