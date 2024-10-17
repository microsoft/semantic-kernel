// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using AotCompatibility.TestApp.JsonSerializerContexts;
using AotCompatibility.TestApp.Plugins;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;

namespace AotCompatibility.TestApp.Tests;

internal sealed class KernelExtensions_KernelPluginTests : BaseTest
{
    private static readonly JsonSerializerOptions s_jsonSerializerOptions = new()
    {
        TypeInfoResolverChain = { WeatherJsonSerializerContext.Default, LocationJsonSerializerContext.Default }
    };

    public static async Task CreateFromType(IConfigurationRoot _)
    {
        // Arrange
        Kernel kernel = new();

        // Act
        KernelPlugin plugin = kernel.CreatePluginFromType<WeatherPlugin>(s_jsonSerializerOptions);

        // Assert
        await AssertGetCurrentWeatherFunctionSchemaAndInvocationResult(kernel, plugin["GetCurrentWeather"]);
    }

    public static async Task CreateFromObject(IConfigurationRoot _)
    {
        // Arrange
        Kernel kernel = new();

        // Act
        KernelPlugin plugin = kernel.CreatePluginFromObject(new WeatherPlugin(), s_jsonSerializerOptions);

        // Assert
        await AssertGetCurrentWeatherFunctionSchemaAndInvocationResult(kernel, plugin["GetCurrentWeather"]);
    }

    public static async Task ImportFromType(IConfigurationRoot _)
    {
        // Arrange
        Kernel kernel = new();

        // Act
        kernel.ImportPluginFromType<WeatherPlugin>(s_jsonSerializerOptions, "weather_utils");

        // Assert
        await AssertGetCurrentWeatherFunctionSchemaAndInvocationResult(kernel, kernel.Plugins["weather_utils"]["GetCurrentWeather"]);
    }

    public static async Task ImportFromObject(IConfigurationRoot _)
    {
        // Arrange
        Kernel kernel = new();

        // Act
        kernel.ImportPluginFromObject(new WeatherPlugin(), s_jsonSerializerOptions, "weather_utils");

        // Assert
        await AssertGetCurrentWeatherFunctionSchemaAndInvocationResult(kernel, kernel.Plugins["weather_utils"]["GetCurrentWeather"]);
    }
}
