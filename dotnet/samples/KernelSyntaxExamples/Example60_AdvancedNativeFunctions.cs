// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Globalization;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;

/**
 * This example shows different ways how to define and execute native functions using custom and primitive types.
 */
// ReSharper disable once InconsistentNaming
public static class Example60_AdvancedNativeFunctions
{
    public static async Task RunAsync()
    {
        await NativeFunctionsChainingAsync();

        await NativeFunctionsPipelineAsync();

        await PrimitiveTypesAutoConversionAsync();
    }

    #region Native Functions Chaining

    /// <summary>
    /// This example executes Function1, which in turn executes Function2.
    /// </summary>
    private static async Task NativeFunctionsChainingAsync()
    {
        Console.WriteLine("Running Native Function Chaining example...");

        var kernel = new KernelBuilder().Build();

        var functions = kernel.ImportFunctions(new FunctionsChainingPlugin(), FunctionsChainingPlugin.PluginName);

        var result = await kernel.RunAsync(functions["Function1"]);
        var customType = result.GetValue<MyCustomType>()!;

        Console.WriteLine(customType.Number); // 2
        Console.WriteLine(customType.Text); // From Function1 + From Function2
    }

    /// <summary>
    /// Plugin example with two native functions, where one function is called from another.
    /// </summary>
    private sealed class FunctionsChainingPlugin
    {
        public const string PluginName = nameof(FunctionsChainingPlugin);

        [SKFunction, SKName("Function1")]
        public async Task<MyCustomType> Function1Async(SKContext context)
        {
            // Execute another function
            var result = await context.Runner.RunAsync(PluginName, "Function2");
            var value = result.GetValue<MyCustomType>()!;

            return new MyCustomType
            {
                Number = 2 * value.Number,
                Text = "From Function1 + " + value.Text
            };
        }

        [SKFunction, SKName("Function2")]
        public static MyCustomType Function2()
        {
            return new MyCustomType
            {
                Number = 1,
                Text = "From Function2"
            };
        }
    }

    #endregion

    #region Native Functions Pipeline

    /// <summary>
    /// This example executes Function1 and Function2 sequentially.
    /// Kernel will pass required parameters to second function as result from first function.
    /// </summary>
    private static async Task NativeFunctionsPipelineAsync()
    {
        Console.WriteLine("Running Native Function Pipeline example...");

        var kernel = new KernelBuilder().Build();

        var functions = kernel.ImportFunctions(new FunctionsPipelinePlugin(), FunctionsPipelinePlugin.PluginName);

        var result = await kernel.RunAsync(functions["Function1"], functions["Function2"]);
        var customType = result.GetValue<MyCustomType>()!;

        Console.WriteLine(customType.Number); // 2
        Console.WriteLine(customType.Text); // From Function1 + From Function2
    }

    /// <summary>
    /// Plugin example with two native functions, which will be called sequentially by Kernel.
    /// </summary>
    private sealed class FunctionsPipelinePlugin
    {
        public const string PluginName = nameof(FunctionsPipelinePlugin);

        [SKFunction, SKName("Function1")]
        public MyCustomType Function1()
        {
            return new MyCustomType
            {
                Number = 1,
                Text = "From Function1"
            };
        }

        [SKFunction, SKName("Function2")]
        public static MyCustomType Function2(MyCustomType customType)
        {
            return new MyCustomType
            {
                Number = customType.Number * 2,
                Text = customType.Text + " + From Function2"
            };
        }
    }

    #endregion

    #region Primitive Types Auto Conversion

    /// <summary>
    /// This example shows how to initialize variables, which will be auto-converted to primitive types
    /// in parameters of native function.
    /// </summary>
    private static async Task PrimitiveTypesAutoConversionAsync()
    {
        Console.WriteLine("Running Primitive Types Auto Conversion example...");

        var kernel = new KernelBuilder().Build();

        var functions = kernel.ImportFunctions(new PrimitiveTypesPlugin(), PrimitiveTypesPlugin.PluginName);

        var contextVariables = new ContextVariables();

        contextVariables["number"] = "2";
        contextVariables["text"] = "From Context Variables";

        var result = await kernel.RunAsync(contextVariables, functions["Function1"]);
        var customType = result.GetValue<MyCustomType>()!;

        Console.WriteLine(customType.Number); // 2
        Console.WriteLine(customType.Text); // From Context Variables
    }

    /// <summary>
    /// Plugin example with native function, which contains two parameters with primitive types.
    /// </summary>
    private sealed class PrimitiveTypesPlugin
    {
        public const string PluginName = nameof(PrimitiveTypesPlugin);

        [SKFunction, SKName("Function1")]
        public MyCustomType Function1(int number, string text)
        {
            return new MyCustomType
            {
                Number = number,
                Text = text
            };
        }
    }

    #endregion

    #region Custom Type

    /// <summary>
    /// In order to use custom types, <see cref="TypeConverter"/> should be specified,
    /// that will convert object instance to string representation.
    /// </summary>
    /// <remarks>
    /// <see cref="TypeConverter"/> is used to represent complex object as meaningful string, so
    /// it can be passed to AI for further processing using semantic functions.
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
#pragma warning disable CA1812 // instantiated by Kernel
    private sealed class MyCustomTypeConverter : TypeConverter
#pragma warning restore CA1812
    {
        public override bool CanConvertFrom(ITypeDescriptorContext? context, Type sourceType) => true;

        /// <summary>
        /// This method is used to convert object from string to actual type. This will allow to pass object to
        /// native function which requires it.
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

    #endregion
}
