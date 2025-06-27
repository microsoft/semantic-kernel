// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using SemanticKernel.IntegrationTests.TestSettings;
using xRetry;
using Xunit;

using ChatMessageContent = Microsoft.SemanticKernel.ChatMessageContent;

namespace SemanticKernel.IntegrationTests.Connectors.Ollama;

public sealed class OllamaChatCompletionFunctionCallingTests : BaseIntegrationTest
{
    // Complex parameters currently don't work (tested against llama3.2 model)
    [Fact(Skip = "For manual verification only")]
    public async Task CanAutoInvokeKernelFunctionsWithComplexTypeParametersAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel();
        kernel.ImportPluginFromFunctions("HelperFunctions",
        [
            kernel.CreateFunctionFromMethod((WeatherParameters parameters) =>
            {
                if (parameters.City.Name == "Dublin" && (parameters.City.Country == "Ireland" || parameters.City.Country == "IE"))
                {
                    return Task.FromResult(42.8); // 42.8 Fahrenheit.
                }

                throw new NotSupportedException($"Weather in {parameters.City.Name} ({parameters.City.Country}) is not supported.");
            }, "Get_Current_Temperature", "Get current temperature."),
        ]);

        PromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

        // Act
        var result = await kernel.InvokePromptAsync("What is the current temperature in Dublin, Ireland, in Fahrenheit?", new(settings));

        // Assert
        Assert.NotNull(result);
        Assert.Contains("42.8", result.GetValue<string>(), StringComparison.InvariantCulture); // The WeatherPlugin always returns 42.8 for Dublin, Ireland.
    }

    [Fact(Skip = "For manual verification only")]
    public async Task CanAutoInvokeKernelFunctionsWithPrimitiveTypeParametersAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel(importHelperPlugin: true);

        PromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

        // Act
        var result = await kernel.InvokePromptAsync("Convert 50 degrees Fahrenheit to Celsius.", new(settings));

        // Assert
        Assert.NotNull(result);
        Assert.Contains("10", result.GetValue<string>(), StringComparison.InvariantCulture);
    }

    [Fact(Skip = "For manual verification only")]
    public async Task CanAutoInvokeKernelFunctionsWithEnumTypeParametersAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel(importHelperPlugin: true);

        PromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

        // Act
        var result = await kernel.InvokePromptAsync("Given the current time of day and weather, what is the likely color of the sky in Boston?", new(settings));

        // Assert
        Assert.NotNull(result);
        Assert.Contains("rain", result.GetValue<string>(), StringComparison.OrdinalIgnoreCase);
    }

    [Fact(Skip = "For manual verification only")]
    public async Task CanAutoInvokeKernelFunctionFromPromptAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel();

        var promptFunction = KernelFunctionFactory.CreateFromPrompt(
            "Your role is always to return this text - 'A Game-Changer for the Transportation Industry'. Don't ask for more details or context.",
            functionName: "FindLatestNews",
            description: "Searches for the latest news.");

        kernel.Plugins.Add(KernelPluginFactory.CreateFromFunctions(
            "NewsProvider",
            "Delivers up-to-date news content.",
            [promptFunction]));

        PromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

        // Act
        var result = await kernel.InvokePromptAsync("Show me the latest news as they are.", new(settings));

        // Assert
        Assert.NotNull(result);
        Assert.Contains("Transportation", result.GetValue<string>(), StringComparison.InvariantCultureIgnoreCase);
    }

    [Fact(Skip = "For manual verification only")]
    public async Task ConnectorAgnosticFunctionCallingModelClassesCanBeUsedForManualFunctionCallingAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel(importHelperPlugin: true);

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Given the current time of day and weather, what is the likely color of the sky in Boston?");

        var settings = new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Required() };

        var sut = kernel.GetRequiredService<IChatCompletionService>();

        // Act
        var messageContent = await sut.GetChatMessageContentAsync(chatHistory, settings, kernel);

        var functionCalls = FunctionCallContent.GetFunctionCalls(messageContent).ToArray();

        while (functionCalls.Length != 0)
        {
            // Adding function call from LLM to chat history
            chatHistory.Add(messageContent);

            // Iterating over the requested function calls and invoking them
            foreach (var functionCall in functionCalls)
            {
                var result = await functionCall.InvokeAsync(kernel);

                chatHistory.Add(result.ToChatMessage());
            }

            // Sending the functions invocation results to the LLM to get the final response
            messageContent = await sut.GetChatMessageContentAsync(chatHistory, settings, kernel);
            functionCalls = FunctionCallContent.GetFunctionCalls(messageContent).ToArray();
        }

        // Assert
        Assert.Contains("rain", messageContent.Content, StringComparison.InvariantCultureIgnoreCase);
    }

    [RetryFact(Skip = "For manual verification only")]
    public async Task ConnectorAgnosticFunctionCallingModelClassesCanPassFunctionExceptionToConnectorAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel(importHelperPlugin: true);

        var chatHistory = new ChatHistory();
        chatHistory.AddSystemMessage("Add the \"Error\" keyword to the response, if you are unable to answer a question or an error has happen.");
        chatHistory.AddUserMessage("Given the current time of day and weather, what is the likely color of the sky in Boston?");

        var settings = new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Required() };

        var completionService = kernel.GetRequiredService<IChatCompletionService>();

        // Act
        var messageContent = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);
        var functionCalls = FunctionCallContent.GetFunctionCalls(messageContent).ToArray();



        while (functionCalls.Length != 0)
        {
            // Adding function call from LLM to chat history
            chatHistory.Add(messageContent);

            // Iterating over the requested function calls and invoking them
            foreach (var functionCall in functionCalls)
            {
                // Simulating an exception
                var exception = new OperationCanceledException("The operation was canceled due to timeout.");

                chatHistory.Add(new FunctionResultContent(functionCall, exception).ToChatMessage());
            }

            // Sending the functions execution results back to the LLM to get the final response
            messageContent = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);
            functionCalls = FunctionCallContent.GetFunctionCalls(messageContent).ToArray();
        }

        // Assert
        Assert.NotNull(messageContent.Content);

        TestHelpers.AssertChatErrorExcuseMessage(messageContent.Content);
    }

    [Fact(Skip = "For manual verification only")]
    public async Task ConnectorAgnosticFunctionCallingModelClassesSupportSimulatedFunctionCallsAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel(importHelperPlugin: true);

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("What is the weather in Boston?");

        var settings = new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

        var completionService = kernel.GetRequiredService<IChatCompletionService>();

        // Act
        // Adding a simulated function call to the connector response message
        var simulatedFunctionCall = new FunctionCallContent("weather-alert", id: "call_123");
        var messageContent = new ChatMessageContent(AuthorRole.Assistant, [simulatedFunctionCall]);

        // Adding a simulated function result to chat history
        var simulatedFunctionResult = "A Tornado Watch has been issued, with potential for severe thunderstorms causing unusual sky colors like green, yellow, or dark gray. Stay informed and follow safety instructions from authorities.";
        chatHistory.Add(new FunctionResultContent(simulatedFunctionCall, simulatedFunctionResult).ToChatMessage());

        // Sending the functions invocation results back to the LLM to get the final response
        messageContent = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);

        // Assert
        Assert.Contains("tornado", messageContent.Content, StringComparison.InvariantCultureIgnoreCase);
    }

    [RetryFact(Skip = "For manual verification only")]
    public async Task ConnectorAgnosticFunctionCallingModelClassesCanBeUsedForAutoFunctionCallingAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel(importHelperPlugin: true);

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Given the current time of day and weather, what is the likely color of the sky in Boston?");

        PromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

        var sut = kernel.GetRequiredService<IChatCompletionService>();

        // Act
        await sut.GetChatMessageContentAsync(chatHistory, settings, kernel);

        // Assert
        var userMessage = chatHistory[0];
        Assert.Equal(AuthorRole.User, userMessage.Role);

        // LLM requested the functions to call.
        var getParallelFunctionCallRequestMessage = chatHistory.First(m => m.Items.Any(i => i is FunctionCallContent));
        Assert.Equal(AuthorRole.Assistant, getParallelFunctionCallRequestMessage.Role);

        // Parallel Function Calls in the same request
        var functionCalls = getParallelFunctionCallRequestMessage.Items.OfType<FunctionCallContent>().ToArray();

        FunctionCallContent getWeatherForCityFunctionCallRequest;
        ChatMessageContent getWeatherForCityFunctionCallResultMessage;

        // Assert
        // LLM requested the current time.
        getWeatherForCityFunctionCallRequest = functionCalls[0];

        // Connector invoked the Get_Weather_For_City function and added result to chat history.
        getWeatherForCityFunctionCallResultMessage = chatHistory.First(m => m.Items.Any(i => i is FunctionResultContent));

        Assert.Equal("HelperFunctions_Get_Weather_For_City", getWeatherForCityFunctionCallRequest.FunctionName);
        Assert.NotNull(getWeatherForCityFunctionCallRequest.Id);

        Assert.Equal(AuthorRole.Tool, getWeatherForCityFunctionCallResultMessage.Role);
        Assert.Single(getWeatherForCityFunctionCallResultMessage.Items.OfType<FunctionResultContent>()); // Current function calling model adds TextContent item representing the result of the function call.

        var getWeatherForCityFunctionCallResult = getWeatherForCityFunctionCallResultMessage.Items.OfType<FunctionResultContent>().Single();
        Assert.Equal("HelperFunctions_Get_Weather_For_City", getWeatherForCityFunctionCallResult.FunctionName);
        Assert.Equal(getWeatherForCityFunctionCallRequest.Id, getWeatherForCityFunctionCallResult.CallId);
        Assert.NotNull(getWeatherForCityFunctionCallResult.Result);
    }

    [Fact(Skip = "For manual verification only")]
    public async Task SubsetOfFunctionsCanBeUsedForFunctionCallingAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel();

        var function = kernel.CreateFunctionFromMethod(() => DayOfWeek.Friday.ToString(), "GetDayOfWeek", "Retrieves the current day of the week.");
        kernel.ImportPluginFromFunctions("HelperFunctions", [function]);

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("What day is today?");

        PromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

        var sut = kernel.GetRequiredService<IChatCompletionService>();

        // Act
        var result = await sut.GetChatMessageContentAsync(chatHistory, settings, kernel);

        // Assert
        Assert.NotNull(result);
        Assert.Contains("Friday", result.Content, StringComparison.InvariantCulture);
    }

    [Fact(Skip = "For manual verification only")]
    public async Task RequiredFunctionShouldBeCalledAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel();

        var function = kernel.CreateFunctionFromMethod(() => DayOfWeek.Friday.ToString(), "GetDayOfWeek", "Retrieves the current day of the week.");
        kernel.ImportPluginFromFunctions("HelperFunctions", [function]);

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("What day is today?");

        PromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

        var sut = kernel.GetRequiredService<IChatCompletionService>();

        // Act
        var result = await sut.GetChatMessageContentAsync(chatHistory, settings, kernel);

        // Assert
        Assert.NotNull(result);
        Assert.Contains("Friday", result.Content, StringComparison.InvariantCulture);
    }

    private Kernel CreateAndInitializeKernel(bool importHelperPlugin = false)
    {
        var config = this._configuration.GetSection("Ollama").Get<OllamaConfiguration>();

        Assert.NotNull(config);
        Assert.NotNull(config.Endpoint);
        Assert.NotNull(config.ModelId ?? "llama3.2");

        var kernelBuilder = base.CreateKernelBuilder();

        kernelBuilder.AddOllamaChatCompletion(
            modelId: config.ModelId ?? "llama3.2",
            endpoint: new Uri(config.Endpoint));

        var kernel = kernelBuilder.Build();

        if (importHelperPlugin)
        {
            kernel.ImportPluginFromFunctions("HelperFunctions",
            [
                kernel.CreateFunctionFromMethod(() => DateTime.UtcNow.ToString("R"), "Get_Current_Utc_Time", "Retrieves the current time in UTC."),
                kernel.CreateFunctionFromMethod((string cityName) =>
                {
                    return cityName switch
                    {
                        "Boston" => "61 and rainy",
                        _ => "31 and snowing",
                    };
                }, "Get_Weather_For_City", "Gets the current weather for the specified city"),
            ]);
        }

        return kernel;
    }

    public record WeatherParameters(City City);

    public class City
    {
        public string Name { get; set; } = string.Empty;
        public string Country { get; set; } = string.Empty;
    }

    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<OllamaChatCompletionFunctionCallingTests>()
        .Build();
}
