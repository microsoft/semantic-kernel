using System;
using System.ComponentModel;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AI.Bedrock;
using Microsoft.Extensions.Configuration;

public class BedrockFunctionExample
{
    private readonly IKernel _kernel;

    public BedrockFunctionExample(IConfiguration configuration)
    {
        string modelId = configuration["AWSBedrockSettings:ModelId"] ?? "anthropic.claude-v2";

        _kernel = Kernel.Builder
            .WithAWSBedrockChatCompletion(modelId)
            .Build();

        // Register native functions
        _kernel.ImportFunctions(new WeatherPlugin(), "Weather");
    }

    public async Task RunFunctionExampleAsync()
    {
        Console.WriteLine("Running function calling example with AWS Bedrock...\n");

        // Create a prompt that will use the weather function
        const string prompt = @"
            Use the available functions to help the user with weather information.
            If you need weather data, use the GetWeather function.
            Be concise in your responses.
            {{$input}}";

        // Create the semantic function
        var promptConfig = new PromptTemplateConfig
        {
            Description = "Assistant that helps with weather information"
        };
        var weatherAssistant = _kernel.CreateFunctionFromPrompt(prompt, promptConfig);

        // Example interactions
        await ProcessUserQuery(weatherAssistant, "What's the weather like in Seattle?");
        await ProcessUserQuery(weatherAssistant, "Should I bring an umbrella in New York today?");
    }

    private async Task ProcessUserQuery(KernelFunction function, string query)
    {
        Console.WriteLine($"User: {query}");
        try
        {
            var result = await _kernel.InvokeAsync(function, new KernelArguments(query));
            Console.WriteLine($"Assistant: {result.GetValue<string>()}\n");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error: {ex.Message}\n");
        }
    }

    public static async Task Main()
    {
        IConfiguration configuration = new ConfigurationBuilder()
            .SetBasePath(Directory.GetCurrentDirectory())
            .AddJsonFile("appsettings.json", optional: false)
            .Build();

        var example = new BedrockFunctionExample(configuration);
        await example.RunFunctionExampleAsync();
    }
}

public class WeatherPlugin
{
    [KernelFunction, Description("Get the current weather for a specific city")]
    public string GetWeather(string city)
    {
        // This is a mock implementation. In a real application,
        // you would call a weather API here
        var random = new Random();
        var temperature = random.Next(0, 35);
        var conditions = new[] { "sunny", "cloudy", "rainy", "windy" };
        var condition = conditions[random.Next(conditions.Length)];

        return $"The weather in {city} is {condition} with a temperature of {temperature}°C";
    }
}