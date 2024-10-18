// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel;
using SemanticKernel.AotTests.JsonSerializerContexts;
using SemanticKernel.AotTests.Plugins;

namespace SemanticKernel.AotTests.UnitTests;

internal sealed class KernelBuilderPluginsExtensionsTests : BaseTest
{
    private static readonly JsonSerializerOptions s_jsonSerializerOptions = new()
    {
        TypeInfoResolverChain = { WeatherJsonSerializerContext.Default, LocationJsonSerializerContext.Default }
    };

    public static async Task AddFromType()
    {
        // Arrange
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();

        // Act
        kernelBuilder.Plugins.AddFromType<WeatherPlugin>(s_jsonSerializerOptions, "weather_utils");

        // Assert
        Kernel kernel = kernelBuilder.Build();
        await AssertGetCurrentWeatherFunctionSchemaAndInvocationResult(kernel, kernel.Plugins["weather_utils"]["GetCurrentWeather"]);
    }

    public static async Task AddFromObject()
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
