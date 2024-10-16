// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using AotCompatibility.TestApp.JsonSerializerContexts;
using AotCompatibility.TestApp.Plugins;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;

namespace AotCompatibility.TestApp.Tests;

internal sealed class KernelBuilderPluginsExtensionsTests : BaseTest
{
    private static readonly JsonSerializerOptions s_jsonSerializerOptions = new()
    {
        TypeInfoResolverChain = { WeatherJsonSerializerContext.Default, LocationJsonSerializerContext.Default }
    };

    public static async Task AddFromType(IConfigurationRoot _)
    {
        // Act
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.Plugins.AddFromType<WeatherPlugin>(s_jsonSerializerOptions, "weather_utils");

        Kernel kernel = kernelBuilder.Build();

        // Assert
        await AssertGetCurrentWeatherFunctionSchemaAndInvocationResult(kernel, kernel.Plugins["weather_utils"]["GetCurrentWeather"]);
    }

    public static async Task AddFromObject(IConfigurationRoot _)
    {
        // Act
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.Plugins.AddFromObject(new WeatherPlugin(), s_jsonSerializerOptions, "weather_utils");

        Kernel kernel = kernelBuilder.Build();

        // Assert
        await AssertGetCurrentWeatherFunctionSchemaAndInvocationResult(kernel, kernel.Plugins["weather_utils"]["GetCurrentWeather"]);
    }
}
