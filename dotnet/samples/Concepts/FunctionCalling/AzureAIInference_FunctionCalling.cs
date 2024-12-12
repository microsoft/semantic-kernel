// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

namespace FunctionCalling;
public class AzureAIInference_FunctionCalling(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// This example demonstrates usage of <see cref="FunctionChoiceBehavior.Auto"/> that advertises all kernel functions to the AI model.
    /// </summary>
    [Fact]
    public async Task FunctionCallingAsync()
    {
        var kernel = CreateKernel();
        PromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };
        Console.WriteLine(await kernel.InvokePromptAsync("Given the current time of day and weather, what is the likely color of the sky in Boston?", new(settings)));
    }

    private static Kernel CreateKernel()
    {
        // Create kernel
        var kernel = Kernel.CreateBuilder()
            .AddAzureAIInferenceChatCompletion(
                modelId: TestConfiguration.AzureAIInference.ChatModelId,
                endpoint: new Uri(TestConfiguration.AzureAIInference.Endpoint),
                apiKey: TestConfiguration.AzureAIInference.ApiKey)
            .Build();

        // Add a plugin with some helper functions we want to allow the model to call.
        kernel.ImportPluginFromFunctions("HelperFunctions",
        [
            kernel.CreateFunctionFromMethod(() => new List<string> { "Squirrel Steals Show", "Dog Wins Lottery" }, "GetLatestNewsTitles", "Retrieves latest news titles."),
            kernel.CreateFunctionFromMethod(() => DateTime.UtcNow.ToString("R"), "GetCurrentUtcDateTime", "Retrieves the current date time in UTC."),
            kernel.CreateFunctionFromMethod((string cityName, string currentDateTime) =>
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
                }, "GetWeatherForCity", "Gets the current weather for the specified city"),
        ]);

        return kernel;
    }
}
