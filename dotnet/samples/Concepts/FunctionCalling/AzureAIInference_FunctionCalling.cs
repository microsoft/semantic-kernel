// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureAIInference;

namespace FunctionCalling;

public class AzureAIInference_FunctionCalling : BaseTest
{
    private readonly LoggingHandler _handler;
    private readonly HttpClient _httpClient;
    private bool _isDisposed;

    public AzureAIInference_FunctionCalling(ITestOutputHelper output) : base(output)
    {
        // Create a logging handler to output HTTP requests and responses
        this._handler = new LoggingHandler(new HttpClientHandler(), this.Output);
        this._httpClient = new(this._handler);
    }

    /// <summary>
    /// This example demonstrates usage of <see cref="FunctionChoiceBehavior.Auto"/> that advertises all kernel functions to the AI model.
    /// </summary>
    [Fact]
    public async Task FunctionCallingAsync()
    {
        var kernel = CreateKernel();
        AzureAIInferencePromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };
        Console.WriteLine(await kernel.InvokePromptAsync("Given the current time of day and weather, what is the likely color of the sky in Boston?", new(settings)));
    }

    /// <summary>
    /// This example demonstrates usage of <see cref="FunctionChoiceBehavior.Auto"/> that advertises all kernel functions to the AI model.
    /// </summary>
    [Fact]
    public async Task FunctionCallingWithPromptExecutionSettingsAsync()
    {
        var kernel = CreateKernel();
        PromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };
        Console.WriteLine(await kernel.InvokePromptAsync("Given the current time of day and weather, what is the likely color of the sky in Boston?", new(settings)));
    }

    protected override void Dispose(bool disposing)
    {
        if (!this._isDisposed)
        {
            if (disposing)
            {
                this._handler.Dispose();
                this._httpClient.Dispose();
            }

            this._isDisposed = true;
        }
        base.Dispose(disposing);
    }

    private Kernel CreateKernel()
    {
        // Create kernel
        var kernel = Kernel.CreateBuilder()
            .AddAzureAIInferenceChatCompletion(
                modelId: TestConfiguration.AzureAIInference.ChatModelId,
                endpoint: new Uri(TestConfiguration.AzureAIInference.Endpoint),
                apiKey: TestConfiguration.AzureAIInference.ApiKey,
                httpClient: this._httpClient)
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
