// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using AotCompatibility.TestApp.JsonSerializerContexts;
using AotCompatibility.TestApp.Plugins;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;

namespace AotCompatibility.TestApp.Tests;

internal sealed class KernelPluginFactoryTests : BaseTest
{
    private static readonly Kernel s_kernel = new();

    private static readonly JsonSerializerOptions s_jsonSerializerOptions = new()
    {
        TypeInfoResolverChain = { WeatherJsonSerializerContext.Default, LocationJsonSerializerContext.Default }
    };

    public static async Task CreateFromType(IConfigurationRoot _)
    {
        // Act
        KernelPlugin plugin = KernelPluginFactory.CreateFromType<WeatherPlugin>(s_jsonSerializerOptions);

        // Assert
        await AssertGetCurrentWeatherFunctionSchemaAndInvocationResult(s_kernel, plugin["GetCurrentWeather"]);
    }

    public static async Task CreateFromObject(IConfigurationRoot _)
    {
        // Act
        KernelPlugin plugin = KernelPluginFactory.CreateFromObject(new WeatherPlugin(), s_jsonSerializerOptions);

        // Assert
        await AssertGetCurrentWeatherFunctionSchemaAndInvocationResult(s_kernel, plugin["GetCurrentWeather"]);
    }
}
