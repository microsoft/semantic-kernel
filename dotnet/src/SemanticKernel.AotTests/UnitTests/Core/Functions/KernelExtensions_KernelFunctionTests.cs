// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using SemanticKernel.AotTests.JsonSerializerContexts;
using SemanticKernel.AotTests.Plugins;

namespace SemanticKernel.AotTests.UnitTests.Core.Functions;

internal sealed class KernelExtensions_KernelFunctionTests
{
    private static readonly Kernel s_kernel = new();

    private static readonly Func<Location, Weather> s_lambda = location => location.City == "Boston" ? new Weather { Temperature = 61, Condition = "rainy" } : throw new NotImplementedException();

    private static readonly JsonSerializerOptions s_jsonSerializerOptions = new()
    {
        TypeInfoResolverChain = { WeatherJsonSerializerContext.Default, LocationJsonSerializerContext.Default }
    };

    public static async Task CreateFromLambda()
    {
        // Act
        KernelFunction function = s_kernel.CreateFunctionFromMethod(s_lambda, s_jsonSerializerOptions);

        // Assert
        await GetWeatherFunctionAsserts.AssertGetCurrentWeatherFunctionSchemaAndInvocationResult(s_kernel, function);
    }

    public static async Task CreateFromMethod()
    {
        // Act
        KernelFunction function = s_kernel.CreateFunctionFromMethod(GetWeather, s_jsonSerializerOptions);

        // Assert
        await GetWeatherFunctionAsserts.AssertGetCurrentWeatherFunctionSchemaAndInvocationResult(s_kernel, function);
    }

    public static async Task CreateFromStringPrompt()
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

        await GetWeatherFunctionAsserts.AssertPromptFunctionSchemaAndInvocationResult(kernel, function);
        await GetWeatherFunctionAsserts.AssertPromptFunctionSchemaAndStreamedInvocationResult(kernel, function);
    }

    public static async Task CreateFromPromptTemplate()
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

        await GetWeatherFunctionAsserts.AssertPromptFunctionSchemaAndInvocationResult(kernel, function);
        await GetWeatherFunctionAsserts.AssertPromptFunctionSchemaAndStreamedInvocationResult(kernel, function);
    }

    private static Weather GetWeather(Location location)
    {
        return location.City == "Boston" ? new Weather { Temperature = 61, Condition = "rainy" } : throw new NotImplementedException();
    }
}
