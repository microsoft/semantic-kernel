// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel;
using SemanticKernel.AotTests.JsonSerializerContexts;
using SemanticKernel.AotTests.Plugins;

namespace SemanticKernel.AotTests.UnitTests.Core.Functions;

internal sealed class KernelFunctionMetadataFactoryTests
{
    private static readonly JsonSerializerOptions s_jsonSerializerOptions = new()
    {
        TypeInfoResolverChain = { WeatherJsonSerializerContext.Default, LocationJsonSerializerContext.Default }
    };

    public static async Task CreateFromType()
    {
        // Act
        IEnumerable<KernelFunctionMetadata> metadata = KernelFunctionMetadataFactory.CreateFromType(typeof(WeatherPlugin), s_jsonSerializerOptions);

        // Assert
        GetWeatherFunctionAsserts.AssertGetCurrentWeatherFunctionMetadata(metadata.Single());
    }
}
