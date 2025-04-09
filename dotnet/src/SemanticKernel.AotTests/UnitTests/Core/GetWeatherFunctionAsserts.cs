// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using Microsoft.SemanticKernel;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using SemanticKernel.AotTests.Plugins;

namespace SemanticKernel.AotTests.UnitTests.Core;

internal static class GetWeatherFunctionAsserts
{
    internal static async Task AssertGetCurrentWeatherFunctionSchemaAndInvocationResult(Kernel kernel, KernelFunction function)
    {
        // Assert input parameter schema  
        AssertGetCurrentWeatherFunctionMetadata(function.Metadata);

        // Assert the function is invocable
        KernelArguments arguments = new() { ["location"] = new Location("USA", "Boston") };

        // Assert the function result
        FunctionResult functionResult = await function.InvokeAsync(kernel, arguments);

        Weather weather = functionResult.GetValue<Weather>()!;
        Assert.AreEqual(61, weather.Temperature);
        Assert.AreEqual("rainy", weather.Condition);
    }

    internal static void AssertGetCurrentWeatherFunctionMetadata(KernelFunctionMetadata metadata)
    {
        // Assert input parameter schema  
        Assert.AreEqual("""{"type":"object","properties":{"Country":{"type":"string"},"City":{"type":"string"}},"required":["Country","City"]}""", metadata.Parameters.Single().Schema!.ToString());

        // Assert return type schema  
        Assert.AreEqual("""{"type":"object","properties":{"Temperature":{"type":["integer","null"]},"Condition":{"type":["string","null"]}}}""", metadata.ReturnParameter.Schema!.ToString());
    }

    internal static async Task AssertPromptFunctionSchemaAndInvocationResult(Kernel kernel, KernelFunction function)
    {
        // Assert parameter type schema
        Assert.AreEqual("{\"type\":\"string\"}", function.Metadata.Parameters[0].Schema!.ToString());

        // Assert return type schema
        Assert.IsNull(function.Metadata.ReturnParameter.Schema);

        // Assert the function is invocable
        KernelArguments arguments = new() { ["location"] = new Location("USA", "Boston") };

        // Assert the function result
        FunctionResult functionResult = await function.InvokeAsync(kernel, arguments);

        Assert.AreEqual("Is it suitable for hiking today? - Current weather(temperature: 61F, condition: rainy)", functionResult.ToString());
    }

    internal static async Task AssertPromptFunctionSchemaAndStreamedInvocationResult(Kernel kernel, KernelFunction function)
    {
        // Assert parameter type schema
        Assert.AreEqual("{\"type\":\"string\"}", function.Metadata.Parameters[0].Schema!.ToString());

        // Assert return type schema
        Assert.IsNull(function.Metadata.ReturnParameter.Schema);

        // Assert the function is invocable
        KernelArguments arguments = new() { ["location"] = new Location("USA", "Boston") };

        StringBuilder contentBuilder = new();

        // Assert the function result
        await foreach (StreamingKernelContent content in function.InvokeStreamingAsync(kernel, arguments))
        {
            contentBuilder.Append(content);
        }

        Assert.AreEqual("Is it suitable for hiking today? - Current weather(temperature: 61F, condition: rainy)", contentBuilder.ToString());
    }
}
