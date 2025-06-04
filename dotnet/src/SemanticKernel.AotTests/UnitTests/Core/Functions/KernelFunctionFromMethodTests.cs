// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel;
using SemanticKernel.AotTests.JsonSerializerContexts;
using SemanticKernel.AotTests.Plugins;

namespace SemanticKernel.AotTests.UnitTests.Core.Functions;

internal sealed class KernelFunctionFromMethodTests
{
    private static readonly Kernel s_kernel = new();

    private static readonly JsonSerializerOptions s_jsonSerializerOptions = new()
    {
        TypeInfoResolverChain = { WeatherJsonSerializerContext.Default, LocationJsonSerializerContext.Default }
    };

    public static async Task CreateUsingOverloadWithFunctionDetails()
    {
        // Act
        KernelFunction function = KernelFunctionFromMethod.Create(((Func<Location, Weather>)GetWeather).Method, s_jsonSerializerOptions, functionName: "f1");

        // Assert
        await GetWeatherFunctionAsserts.AssertGetCurrentWeatherFunctionSchemaAndInvocationResult(s_kernel, function);
    }

    public static async Task CreateUsingOverloadWithOptions()
    {
        // Act
        KernelFunction function = KernelFunctionFromMethod.Create(((Func<Location, Weather>)GetWeather).Method, s_jsonSerializerOptions, options: new KernelFunctionFromMethodOptions());

        // Assert
        await GetWeatherFunctionAsserts.AssertGetCurrentWeatherFunctionSchemaAndInvocationResult(s_kernel, function);
    }

    public static Task CreateMetadataUsingOverloadWithFunctionDetails()
    {
        // Act
        KernelFunctionMetadata metadata = KernelFunctionFromMethod.CreateMetadata(((Func<Location, Weather>)GetWeather).Method, s_jsonSerializerOptions, functionName: "f1");

        // Assert
        GetWeatherFunctionAsserts.AssertGetCurrentWeatherFunctionMetadata(metadata);
        return Task.CompletedTask;
    }

    public static Task CreateMetadataUsingOverloadWithOptions()
    {
        // Act
        KernelFunctionMetadata metadata = KernelFunctionFromMethod.CreateMetadata(((Func<Location, Weather>)GetWeather).Method, s_jsonSerializerOptions, options: new KernelFunctionFromMethodOptions());

        // Assert
        GetWeatherFunctionAsserts.AssertGetCurrentWeatherFunctionMetadata(metadata);
        return Task.CompletedTask;
    }

    private static Weather GetWeather(Location location)
    {
        return location.City == "Boston" ? new Weather { Temperature = 61, Condition = "rainy" } : throw new NotImplementedException();
    }
}
