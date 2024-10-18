// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel;
using SemanticKernel.AotTests.JsonSerializerContexts;
using SemanticKernel.AotTests.Plugins;

namespace SemanticKernel.AotTests.UnitTests;

internal sealed class KernelPluginFactoryTests : BaseTest
{
    private static readonly Kernel s_kernel = new();

    private static readonly JsonSerializerOptions s_jsonSerializerOptions = new()
    {
        TypeInfoResolverChain = { WeatherJsonSerializerContext.Default, LocationJsonSerializerContext.Default }
    };

    public static async Task CreateFromType()
    {
        // Act
        KernelPlugin plugin = KernelPluginFactory.CreateFromType<WeatherPlugin>(s_jsonSerializerOptions);

        // Assert
        await AssertGetCurrentWeatherFunctionSchemaAndInvocationResult(s_kernel, plugin["GetCurrentWeather"]);
    }

    public static async Task CreateFromObject()
    {
        // Act
        KernelPlugin plugin = KernelPluginFactory.CreateFromObject(new WeatherPlugin(), s_jsonSerializerOptions);

        // Assert
        await AssertGetCurrentWeatherFunctionSchemaAndInvocationResult(s_kernel, plugin["GetCurrentWeather"]);
    }
}
