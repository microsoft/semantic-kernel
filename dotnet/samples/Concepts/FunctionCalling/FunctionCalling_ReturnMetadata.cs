// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace FunctionCalling;

/// <summary>
/// These samples illustrate how function return type metadata can be communicated to the AI model, allowing it to reason about the function's return value.
/// Currently, there is no well-defined, industry-wide standard for providing function return type metadata to AI models.
/// Until such a standard is established, the following techniques can be considered for scenarios where the names of return type properties are insufficient
/// for AI models to reason about their content, or where additional context or handling instructions need to be associated with the return type to model or enhance
/// your scenarios.
/// </summary>
/// <remarks>
/// The properties of the WeatherData classes used in the samples are intentionally given generic names(e.g., Data1, Data2, Data3, Data4) to abstract their meanings
/// for samples purposes only.This approach prevents the model from making assumptions about their content based solely on their names and encourages the model to
/// utilize other return type metadata, such as descriptions or schemas, to reason about their content.
/// Before employing any of these techniques, it is recommended to ensure that the property names of the return types of your functions are descriptive enough
/// to convey their purpose/content.
/// </remarks>
public class FunctionCalling_ReturnMetadata(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    /// <summary>
    /// This sample demonstrates how to describe the return type of a function to the AI model using the function description attribute.
    /// </summary>
    /// <remarks>
    /// This information is provided to the AI model during the function advertisement step.
    /// The description includes only the property names and their descriptions, without any type information.
    /// This approach may be useful when type information is not critical and minimizing token consumption is a priority.
    /// Additionally, type information in the description must be added manually and updated each time the return type changes.
    /// </remarks>
    public async Task ProvideFunctionReturnTypeDescriptionInFunctionDescriptionAsync()
    {
        Kernel kernel = CreateKernel();

        // Import plugin that has a return type described in the function description.
        kernel.ImportPluginFromType<WeatherPlugin1>();

        OpenAIPromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

        FunctionResult result = await kernel.InvokePromptAsync("What is the current weather?", new(settings));

        Console.WriteLine(result);
        // Output: The current weather is as follows:
        // - Temperature: 35°C
        // - Humidity: 20%
        // - Dew Point: 10°C
        // - Wind Speed: 15 km/h
    }

    [Fact]
    /// <summary>
    /// This sample demonstrates how to provide the return type schema of a function to the AI model using the function description attribute.
    /// </summary>
    /// <remarks>
    /// This information is supplied to the AI model during the function advertisement step.
    /// The description includes the return type schema in JSON format, detailing the property names, descriptions, and types.
    /// This approach is recommended when type information is essential.
    /// As with the previous sample, the return type schema must be added manually and updated each time the return type changes.
    /// </remarks>
    public async Task ProvideFunctionReturnTypeSchemaInFunctionDescriptionAsync()
    {
        Kernel kernel = CreateKernel();

        // Import plugin that has a return type schema in the function description.
        kernel.ImportPluginFromType<WeatherPlugin2>();

        OpenAIPromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

        FunctionResult result = await kernel.InvokePromptAsync("What is the current weather?", new(settings));

        Console.WriteLine(result);
        // Output: The current weather details is as follows:
        // - Temperature: 35°C
        // - Humidity: 20%
        // - Dew Point: 10°C
        // - Wind Speed: 15 km/h
    }

    [Fact]
    /// <summary>
    /// This sample demonstrates how to provide the return type schema of a function to the AI model as part of the function's return value.
    /// </summary>
    /// <remarks>
    /// This information is supplied to the AI model during the function invocation step, rather than during the function advertisement step.
    /// This approach can help reduce token consumption, particularly in situations where only a few out of many available functions are called.
    /// The return type schema for the functions invoked by the AI model will be returned to the AI model along with the invocation result,
    /// while the schemas for the return types of functions that were not invoked will never be provided.
    /// This method does not require the return type schema to be provided manually and updated each time the return type changes, as the schema
    /// is extracted automatically by SK.
    /// </remarks>
    public async Task ProvideFunctionReturnTypeSchemaAsPartOfFunctionReturnValueAsync()
    {
        Kernel kernel = CreateKernel();

        /// Register the auto function invocation filter that replaces the original function's result
        /// with a new result that includes both the original result and its schema.
        kernel.AutoFunctionInvocationFilters.Add(new AddReturnTypeSchemaFilter());

        // Import the plugin that provides descriptions for the return type properties.   
        // This additional information is used when extracting the schema from the return type.
        kernel.ImportPluginFromType<WeatherPlugin3>();

        OpenAIPromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

        FunctionResult result = await kernel.InvokePromptAsync("What is the current weather?", new(settings));

        Console.WriteLine(result);
        // Output: The current weather conditions are as follows:
        // - Temperature: 35°C
        // - Humidity: 20 %
        // - Dew Point: 10°C
        // - Wind Speed: 15 km/h
    }

    /// <summary>
    /// A plugin that provides the current weather data and describes the return type in the function <see cref="DescriptionAttribute"/>.
    /// </summary>
    private sealed class WeatherPlugin1
    {
        [KernelFunction]
        [Description("Returns current weather: Data1 - Temperature (°C), Data2 - Humidity (%), Data3 - Dew Point (°C), Data4 - Wind Speed (km/h)")]
        public WeatherData GetWeatherData()
        {
            return new WeatherData()
            {
                Data1 = 35.0,  // Temperature in degrees Celsius  
                Data2 = 20.0,  // Humidity in percentage  
                Data3 = 10.0,  // Dew point in degrees Celsius  
                Data4 = 15.0   // Wind speed in kilometers per hour
            };
        }
        public sealed class WeatherData
        {
            public double Data1 { get; set; }
            public double Data2 { get; set; }
            public double Data3 { get; set; }
            public double Data4 { get; set; }
        }
    }

    /// <summary>
    /// A plugin that provides the current weather data and specifies the return type schema in the function <see cref="DescriptionAttribute"/>.
    /// </summary>
    private sealed class WeatherPlugin2
    {
        [KernelFunction]
        [Description("""Returns current weather: {"type":"object","properties":{"Data1":{"description":"Temperature (°C)","type":"number"},"Data2":{"description":"Humidity(%)","type":"number"}, Data3":{"description":"Dew point (°C)","type":"number"},"Data4":{"description":"Wind speed (km/h)","type":"number"}}}""")]
        public WeatherData GetWeatherData()
        {
            return new WeatherData()
            {
                Data1 = 35.0,  // Temperature in degrees Celsius  
                Data2 = 20.0,  // Humidity in percentage  
                Data3 = 10.0,  // Dew point in degrees Celsius  
                Data4 = 15.0   // Wind speed in kilometers per hour
            };
        }

        public sealed class WeatherData
        {
            public double Data1 { get; set; }
            public double Data2 { get; set; }
            public double Data3 { get; set; }
            public double Data4 { get; set; }
        }
    }

    /// <summary>
    /// A plugin that provides the current weather data and provides descriptions for the return type properties.
    /// </summary>
    private sealed class WeatherPlugin3
    {
        [KernelFunction]
        public WeatherData GetWeatherData()
        {
            return new WeatherData()
            {
                Data1 = 35.0,  // Temperature in degrees Celsius  
                Data2 = 20.0,  // Humidity in percentage  
                Data3 = 10.0,  // Dew point in degrees Celsius  
                Data4 = 15.0   // Wind speed in kilometers per hour
            };
        }

        public sealed class WeatherData
        {
            [Description("Temp (°C)")]
            public double Data1 { get; set; }

            [Description("Humidity (%)")]
            public double Data2 { get; set; }

            [Description("Dew point (°C)")]
            public double Data3 { get; set; }

            [Description("Wind speed (km/h)")]
            public double Data4 { get; set; }
        }
    }

    /// <summary>
    /// A auto function invocation filter that replaces the original function's result with a new result that includes both the original result and its schema.
    /// </summary>
    private sealed class AddReturnTypeSchemaFilter : IAutoFunctionInvocationFilter
    {
        public async Task OnAutoFunctionInvocationAsync(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next)
        {
            // Invoke the function
            await next(context);

            // Crete the result with the schema
            FunctionResultWithSchema resultWithSchema = new()
            {
                Value = context.Result.GetValue<object>(),                  // Get the original result
                Schema = context.Function.Metadata.ReturnParameter?.Schema  // Get the function return type schema
            };

            // Return the result with the schema instead of the original one
            context.Result = new FunctionResult(context.Result, resultWithSchema);
        }

        private sealed class FunctionResultWithSchema
        {
            public object? Value { get; set; }

            public KernelJsonSchema? Schema { get; set; }
        }
    }

    /// <summary>
    /// Create a new instance of the <see cref="Kernel"/> with the OpenAI chat completion service.
    /// </summary>
    private static Kernel CreateKernel()
    {
        // Create kernel
        IKernelBuilder builder = Kernel.CreateBuilder();

        builder.AddOpenAIChatCompletion(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey);

        return builder.Build();
    }
}
