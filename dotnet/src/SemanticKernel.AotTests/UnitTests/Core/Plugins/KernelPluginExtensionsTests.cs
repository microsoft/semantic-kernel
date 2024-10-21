// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel;
using SemanticKernel.AotTests.JsonSerializerContexts;
using SemanticKernel.AotTests.Plugins;

namespace SemanticKernel.AotTests.UnitTests.Core.Plugins;

internal sealed class KernelPluginExtensionsTests
{
    private static readonly JsonSerializerOptions s_jsonSerializerOptions = new()
    {
        TypeInfoResolverChain = { WeatherJsonSerializerContext.Default, LocationJsonSerializerContext.Default }
    };

    public static async Task AddFromType()
    {
        // Arrange
        Kernel kernel = new();

        // Act
        kernel.Plugins.AddFromType<WeatherPlugin>(s_jsonSerializerOptions, "weather_utils");

        // Assert
        await GetWeatherFunctionAsserts.AssertGetCurrentWeatherFunctionSchemaAndInvocationResult(kernel, kernel.Plugins["weather_utils"]["GetCurrentWeather"]);
    }

    public static async Task AddFromObject()
    {
        // Arrange
        Kernel kernel = new();

        // Act
        kernel.Plugins.AddFromObject(new WeatherPlugin(), s_jsonSerializerOptions, "weather_utils");

        // Assert
        await GetWeatherFunctionAsserts.AssertGetCurrentWeatherFunctionSchemaAndInvocationResult(kernel, kernel.Plugins["weather_utils"]["GetCurrentWeather"]);
    }
}
