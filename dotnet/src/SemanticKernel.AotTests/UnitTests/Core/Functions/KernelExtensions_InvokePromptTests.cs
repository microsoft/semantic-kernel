// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using System.Text.Json;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using SemanticKernel.AotTests.JsonSerializerContexts;
using SemanticKernel.AotTests.Plugins;

namespace SemanticKernel.AotTests.UnitTests.Core.Functions;

internal sealed class KernelExtensions_InvokePromptTests
{
    private static readonly JsonSerializerOptions s_jsonSerializerOptions = new()
    {
        TypeInfoResolverChain = { WeatherJsonSerializerContext.Default, LocationJsonSerializerContext.Default }
    };

    public static async Task InvokePrompt()
    {
        // Arrange
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.Services.AddSingleton<IChatCompletionService>(new PromptEchoChatCompletionService());
        kernelBuilder.Plugins.Add(KernelPluginFactory.CreateFromType<WeatherPlugin>(s_jsonSerializerOptions, "weather_utils"));

        string prompt = "Is it suitable for hiking today? - {{weather_utils.GetCurrentWeather location=$location}}";

        Kernel kernel = kernelBuilder.Build();

        KernelArguments arguments = new() { ["location"] = new Location("USA", "Boston") };

        // Act
        FunctionResult functionResult = await kernel.InvokePromptAsync(s_jsonSerializerOptions, prompt, arguments);

        // Assert
        Assert.AreEqual("Is it suitable for hiking today? - Current weather(temperature: 61F, condition: rainy)", functionResult.ToString());
    }

    public static async Task InvokePromptStreaming()
    {
        // Arrange
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.Services.AddSingleton<IChatCompletionService>(new PromptEchoChatCompletionService());
        kernelBuilder.Plugins.Add(KernelPluginFactory.CreateFromType<WeatherPlugin>(s_jsonSerializerOptions, "weather_utils"));

        string prompt = "Is it suitable for hiking today? - {{weather_utils.GetCurrentWeather location=$location}}";

        Kernel kernel = kernelBuilder.Build();

        KernelArguments arguments = new() { ["location"] = new Location("USA", "Boston") };

        StringBuilder contentBuilder = new();

        // Act
        await foreach (StreamingKernelContent content in kernel.InvokePromptStreamingAsync(s_jsonSerializerOptions, prompt, arguments))
        {
            contentBuilder.Append(content);
        }

        // Assert
        Assert.AreEqual("Is it suitable for hiking today? - Current weather(temperature: 61F, condition: rainy)", contentBuilder.ToString());
    }
}
