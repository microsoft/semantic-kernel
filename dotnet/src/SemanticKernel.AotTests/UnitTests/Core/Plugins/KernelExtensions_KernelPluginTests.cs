// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel;
using SemanticKernel.AotTests.JsonSerializerContexts;
using SemanticKernel.AotTests.Plugins;

namespace SemanticKernel.AotTests.UnitTests.Core.Plugins;

internal sealed class KernelExtensions_KernelPluginTests
{
    private static readonly JsonSerializerOptions s_jsonSerializerOptions = new()
    {
        TypeInfoResolverChain = { WeatherJsonSerializerContext.Default, LocationJsonSerializerContext.Default }
    };

    public static async Task CreateFromType()
    {
        // Arrange
        Kernel kernel = new();

        // Act
        KernelPlugin plugin = kernel.CreatePluginFromType<WeatherPlugin>(s_jsonSerializerOptions);

        // Assert
        await GetWeatherFunctionAsserts.AssertGetCurrentWeatherFunctionSchemaAndInvocationResult(kernel, plugin["GetCurrentWeather"]);
    }

    public static async Task CreateFromObject()
    {
        // Arrange
        Kernel kernel = new();

        // Act
        KernelPlugin plugin = kernel.CreatePluginFromObject(new WeatherPlugin(), s_jsonSerializerOptions);

        // Assert
        await GetWeatherFunctionAsserts.AssertGetCurrentWeatherFunctionSchemaAndInvocationResult(kernel, plugin["GetCurrentWeather"]);
    }

    public static async Task ImportFromType()
    {
        // Arrange
        Kernel kernel = new();

        // Act
        kernel.ImportPluginFromType<WeatherPlugin>(s_jsonSerializerOptions, "weather_utils");

        // Assert
        await GetWeatherFunctionAsserts.AssertGetCurrentWeatherFunctionSchemaAndInvocationResult(kernel, kernel.Plugins["weather_utils"]["GetCurrentWeather"]);
    }

    public static async Task ImportFromObject()
    {
        // Arrange
        Kernel kernel = new();

        // Act
        kernel.ImportPluginFromObject(new WeatherPlugin(), s_jsonSerializerOptions, "weather_utils");

        // Assert
        await GetWeatherFunctionAsserts.AssertGetCurrentWeatherFunctionSchemaAndInvocationResult(kernel, kernel.Plugins["weather_utils"]["GetCurrentWeather"]);
    }
}
