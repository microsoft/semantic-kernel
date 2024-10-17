// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using System.Text.Json;
using AotCompatibility.TestApp.JsonSerializerContexts;
using AotCompatibility.TestApp.Plugins;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace AotCompatibility.TestApp.Tests;

internal sealed class KernelExtensions_KernelFunctionTests : BaseTest
{
    private static readonly Kernel s_kernel = new();

    private static readonly Func<Location, Weather> s_lambda = location => location.City == "Boston" ? new Weather { Temperature = 61, Condition = "rainy" } : throw new NotImplementedException();

    private static readonly JsonSerializerOptions s_jsonSerializerOptions = new()
    {
        TypeInfoResolverChain = { WeatherJsonSerializerContext.Default, LocationJsonSerializerContext.Default }
    };

    public static async Task CreateFromLambda(IConfigurationRoot _)
    {
        // Act
        KernelFunction function = s_kernel.CreateFunctionFromMethod(s_lambda, s_jsonSerializerOptions);

        // Assert
        await AssertGetCurrentWeatherFunctionSchemaAndInvocationResult(s_kernel, function);
    }

    public static async Task CreateFromMethod(IConfigurationRoot _)
    {
        // Act
        KernelFunction function = s_kernel.CreateFunctionFromMethod(GetWeather, s_jsonSerializerOptions);

        // Assert
        await AssertGetCurrentWeatherFunctionSchemaAndInvocationResult(s_kernel, function);
    }

    public static async Task CreateFromStringPrompt(IConfigurationRoot _)
    {
        // Arrange
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.Services.AddSingleton<IChatCompletionService>(new PromptEchoChatCompletionService());
        kernelBuilder.Plugins.Add(KernelPluginFactory.CreateFromType<WeatherPlugin>(s_jsonSerializerOptions, "weather_utils"));

        string prompt = "Is it suitable for hiking today? - {{weather_utils.GetCurrentWeather location=$location}}";

        // Act
        KernelFunction function = s_kernel.CreateFunctionFromPrompt(prompt, s_jsonSerializerOptions);

        // Assert
        Kernel kernel = kernelBuilder.Build();

        await AssertPromptFunctionSchemaAndInvocationResult(kernel, function);
        await AssertPromptFunctionSchemaAndStreamedInvocationResult(kernel, function);
    }

    public static async Task CreateFromPromptTemplate(IConfigurationRoot _)
    {
        // Arrange
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.Services.AddSingleton<IChatCompletionService>(new PromptEchoChatCompletionService());
        kernelBuilder.Plugins.Add(KernelPluginFactory.CreateFromType<WeatherPlugin>(s_jsonSerializerOptions, "weather_utils"));

        PromptTemplateConfig promptTemplateConfig = new("Is it suitable for hiking today? - {{weather_utils.GetCurrentWeather location=$location}}");

        // Act
        KernelFunction function = s_kernel.CreateFunctionFromPrompt(promptTemplateConfig, s_jsonSerializerOptions);

        // Assert
        Kernel kernel = kernelBuilder.Build();

        await AssertPromptFunctionSchemaAndInvocationResult(kernel, function);
        await AssertPromptFunctionSchemaAndStreamedInvocationResult(kernel, function);
    }

    private static Weather GetWeather(Location location)
    {
        return location.City == "Boston" ? new Weather { Temperature = 61, Condition = "rainy" } : throw new NotImplementedException();
    }

    private static async Task AssertPromptFunctionSchemaAndStreamedInvocationResult(Kernel kernel, KernelFunction function)
    {
        // Assert parameter type schema
        Assert.AreEqual("{\"type\":\"string\"}", function.Metadata.Parameters[0].Schema!.ToString());

        // Assert return type schema
        Assert.IsNull(function.Metadata.ReturnParameter.Schema);

        // Assert the function is invocable
        KernelArguments arguments = new() { ["location"] = new Location("USA", "Boston") };

        StringBuilder contentBuilder = new();

        // Assert the function result
        await foreach (StreamingKernelContent content in function.InvokeStreamingAsync(kernel, arguments))
        {
            contentBuilder.Append(content);
        }

        Assert.AreEqual("Is it suitable for hiking today? - Current weather(temperature: 61F, condition: rainy)", contentBuilder.ToString());
    }
}
