// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Globalization;
using System.Reflection;
using System.Text.Json;
using Microsoft.SemanticKernel;

namespace Functions;

/// <summary>
/// These samples show advanced usage of method functions.
/// </summary>
public class MethodFunctions_Advanced(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// This example executes Function1, which in turn executes Function2.
    /// </summary>
    [Fact]
    public async Task MethodFunctionsChaining()
    {
        Console.WriteLine("Running Method Function Chaining example...");

        var kernel = new Kernel();

        var functions = kernel.ImportPluginFromType<Plugin>();

        var customType = await kernel.InvokeAsync<MyCustomType>(functions["Function1"]);

        Console.WriteLine($"CustomType.Number: {customType!.Number}"); // 2
        Console.WriteLine($"CustomType.Text: {customType.Text}"); // From Function1 + From Function2
    }

    /// <summary>
    /// This example shows how to access the custom <see cref="InvocationSettingsAttribute"/> attribute the underlying method wrapped by Kernel Function is annotated with.
    /// </summary>
    [Fact]
    public async Task AccessUnderlyingMethodAttributes()
    {
        // Import the plugin containing the method with the InvocationSettingsAttribute custom attribute
        var kernel = new Kernel();

        var functions = kernel.ImportPluginFromType<Plugin>();

        // Get the kernel function wrapping the method with the InvocationSettingsAttribute
        var kernelFunction = functions[nameof(Plugin.FunctionWithInvocationSettingsAttribute)];

        // Access the custom attribute the underlying method is annotated with
        var invocationSettingsAttribute = kernelFunction.UnderlyingMethod!.GetCustomAttribute<InvocationSettingsAttribute>();

        Console.WriteLine($"Priority: {invocationSettingsAttribute?.Priority}");
    }

    private sealed class Plugin
    {
        private const string PluginName = nameof(Plugin);

        [KernelFunction]
        public async Task<MyCustomType> Function1Async(Kernel kernel)
        {
            // Execute another function
            var value = await kernel.InvokeAsync<MyCustomType>(PluginName, "Function2");

            return new MyCustomType
            {
                Number = 2 * value?.Number ?? 0,
                Text = "From Function1 + " + value?.Text
            };
        }

        [KernelFunction]
        public static MyCustomType Function2()
        {
            return new MyCustomType
            {
                Number = 1,
                Text = "From Function2"
            };
        }

        [KernelFunction, InvocationSettingsAttribute(priority: Priority.High)]
        public static void FunctionWithInvocationSettingsAttribute()
        {
        }
    }

    /// <summary>
    /// In order to use custom types, <see cref="TypeConverter"/> should be specified,
    /// that will convert object instance to string representation.
    /// </summary>
    /// <remarks>
    /// <see cref="TypeConverter"/> is used to represent complex object as meaningful string, so
    /// it can be passed to AI for further processing using prompt functions.
    /// It's possible to choose any format (e.g. XML, JSON, YAML) to represent your object.
    /// </remarks>
    [TypeConverter(typeof(MyCustomTypeConverter))]
    private sealed class MyCustomType
    {
        public int Number { get; set; }

        public string? Text { get; set; }
    }

    /// <summary>
    /// Implementation of <see cref="TypeConverter"/> for <see cref="MyCustomType"/>.
    /// In this example, object instance is serialized with <see cref="JsonSerializer"/> from System.Text.Json,
    /// but it's possible to convert object to string using any other serialization logic.
    /// </summary>
    private sealed class MyCustomTypeConverter : TypeConverter
    {
        public override bool CanConvertFrom(ITypeDescriptorContext? context, Type sourceType) => true;

        /// <summary>
        /// This method is used to convert object from string to actual type. This will allow to pass object to
        /// method function which requires it.
        /// </summary>
        public override object? ConvertFrom(ITypeDescriptorContext? context, CultureInfo? culture, object value)
        {
            return JsonSerializer.Deserialize<MyCustomType>((string)value);
        }

        /// <summary>
        /// This method is used to convert actual type to string representation, so it can be passed to AI
        /// for further processing.
        /// </summary>
        public override object? ConvertTo(ITypeDescriptorContext? context, CultureInfo? culture, object? value, Type destinationType)
        {
            return JsonSerializer.Serialize(value);
        }
    }

    [AttributeUsage(AttributeTargets.Method)]
    private sealed class InvocationSettingsAttribute : Attribute
    {
        public InvocationSettingsAttribute(Priority priority = Priority.Normal)
        {
            this.Priority = priority;
        }

        public Priority Priority { get; }
    }

    private enum Priority
    {
        Normal,
        High,
    }
}
