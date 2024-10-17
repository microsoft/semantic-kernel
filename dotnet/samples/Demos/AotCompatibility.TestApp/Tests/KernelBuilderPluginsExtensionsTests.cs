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
        // Arrange
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();

        // Act
        kernelBuilder.Plugins.AddFromType<WeatherPlugin>(s_jsonSerializerOptions, "weather_utils");

        // Assert
        Kernel kernel = kernelBuilder.Build();
        await AssertGetCurrentWeatherFunctionSchemaAndInvocationResult(kernel, kernel.Plugins["weather_utils"]["GetCurrentWeather"]);
    }

    public static async Task AddFromObject(IConfigurationRoot _)
    {
        // Arrange
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();

        // Act
        kernelBuilder.Plugins.AddFromObject(new WeatherPlugin(), s_jsonSerializerOptions, "weather_utils");

        // Assert
        Kernel kernel = kernelBuilder.Build();
        await AssertGetCurrentWeatherFunctionSchemaAndInvocationResult(kernelBuilder.Build(), kernel.Plugins["weather_utils"]["GetCurrentWeather"]);
    }
}
