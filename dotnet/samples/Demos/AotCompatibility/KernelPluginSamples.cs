// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using SemanticKernel.AotCompatibility.JsonSerializerContexts;
using SemanticKernel.AotCompatibility.Plugins;

namespace SemanticKernel.AotCompatibility;

/// <summary>
/// This class contains samples of how to create, import and add kernel plugins and invoke their functions in AOT applications.
/// </summary>
internal static class KernelPluginSamples
{
    /// <summary>
    /// Creates a kernel plugin from a type and invokes its function.
    /// </summary>
    /// <remarks>
    /// The KernelPluginFactory class provides other methods such as CreateFromObject and CreateFromFunctions,
    /// which can be used to create a plugin from a class instance or a list of functions.
    /// Additionally, the Kernel.CreatePluginFrom* extension methods are available for similar purposes.
    /// </remarks>
    public static async Task CreatePluginFromType(IConfigurationRoot _)
    {
        Kernel kernel = new();

        // Create JsonSerializerOptions with custom JsonSerializerContexts for the Location and Weather types that are used by the plugin below.
        // This is necessary for JsonSerializer to infer the type information for these types in AOT applications.  
        JsonSerializerOptions options = new();
        options.TypeInfoResolverChain.Add(WeatherJsonSerializerContext.Default);
        options.TypeInfoResolverChain.Add(LocationJsonSerializerContext.Default);

        // Create a kernel plugin
        KernelPlugin plugin = KernelPluginFactory.CreateFromType<WeatherPlugin>(options, "weather_utils");

        // Invoke the function
        KernelFunction function = plugin["GetCurrentWeather"];
        KernelArguments arguments = new() { ["location"] = new Location("USA", "Boston") };

        FunctionResult functionResult = await function.InvokeAsync(kernel, arguments);

        // Display the result
        Weather weather = functionResult.GetValue<Weather>()!;
        Console.WriteLine($"Temperature: {weather.Temperature}, Condition: {weather.Condition}");
    }

    /// <summary>
    /// Imports a kernel plugin into the kernel's plugin collection from a type and invokes its function.
    /// </summary>
    /// <remarks>
    /// The kernel provides extension methods like ImportFromObject, ImportFromFunctions and ImportPluginFromPromptDirectory,
    /// allowing the import of a plugin from a class instance, a collection of functions or a prompt directory.
    /// </remarks>
    public static async Task ImportPluginFromType(IConfigurationRoot _)
    {
        Kernel kernel = new();

        // Create JsonSerializerOptions with custom JsonSerializerContexts for the Location and Weather types that are used by the plugin below.
        // This is necessary for JsonSerializer to infer the type information for these types in AOT applications.  
        JsonSerializerOptions options = new();
        options.TypeInfoResolverChain.Add(WeatherJsonSerializerContext.Default);
        options.TypeInfoResolverChain.Add(LocationJsonSerializerContext.Default);

        // Create a kernel plugin
        KernelPlugin plugin = kernel.ImportPluginFromType<WeatherPlugin>(options, "weather_utils");

        // Invoke the function
        KernelFunction function = kernel.Plugins["weather_utils"]["GetCurrentWeather"];
        KernelArguments arguments = new() { ["location"] = new Location("USA", "Boston") };

        FunctionResult functionResult = await function.InvokeAsync(kernel, arguments);

        // Display the result
        Weather weather = functionResult.GetValue<Weather>()!;
        Console.WriteLine($"Temperature: {weather.Temperature}, Condition: {weather.Condition}");
    }

    /// <summary>
    /// Adds a kernel plugin into the kernel's plugin collection from a type and invokes its function.
    /// </summary>
    /// <remarks>
    /// Other extension methods like AddFromObject, AddFromFunctions
    /// can be used to create a plugin and add it to the kernel's plugins collection.
    /// </remarks>
    public static async Task AddPluginFromType(IConfigurationRoot _)
    {
        Kernel kernel = new();

        // Create JsonSerializerOptions with custom JsonSerializerContexts for the Location and Weather types that are used by the plugin below.
        // This is necessary for JsonSerializer to infer the type information for these types in AOT applications.  
        JsonSerializerOptions options = new();
        options.TypeInfoResolverChain.Add(WeatherJsonSerializerContext.Default);
        options.TypeInfoResolverChain.Add(LocationJsonSerializerContext.Default);

        // Create a kernel plugin
        KernelPlugin plugin = kernel.Plugins.AddFromType<WeatherPlugin>(options, "weather_utils");

        // Invoke the function
        KernelFunction function = kernel.Plugins["weather_utils"]["GetCurrentWeather"];
        KernelArguments arguments = new() { ["location"] = new Location("USA", "Boston") };

        FunctionResult functionResult = await function.InvokeAsync(kernel, arguments);

        // Display the result
        Weather weather = functionResult.GetValue<Weather>()!;
        Console.WriteLine($"Temperature: {weather.Temperature}, Condition: {weather.Condition}");
    }
}
