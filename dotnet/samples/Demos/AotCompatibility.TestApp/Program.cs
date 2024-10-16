// Copyright (c) Microsoft. All rights reserved.

using AotCompatibility.TestApp.Samples;
using AotCompatibility.TestApp.Tests;
using Microsoft.Extensions.Configuration;

namespace AotCompatibility.TestApp;

/// <summary>
/// This application is created in accordance with the instructions in the blog post at https://devblogs.microsoft.com/dotnet/creating-aot-compatible-libraries to ensure that
/// all Native-AOT-related warnings missed by the Roslyn analyzers are caught by the AOT compiler used in this application.
/// </summary>
internal sealed class Program
{
    private static async Task<int> Main(string[] args)
    {
        var config = new ConfigurationBuilder().AddUserSecrets<Program>().Build();

        bool success;

        if (Array.Exists(args, arg => arg == "-tests"))
        {
            success = await RunAsync(s_tests, config);
        }
        else
        {
            success = await RunAsync(s_samples, config);
        }

        return success ? 1 : 0;
    }

    private static readonly Func<IConfigurationRoot, Task>[] s_samples =
    [
        // Samples showing how to create a kernel function and invoke it in AOT applications.
        KernelFunctionSamples.CreateFunctionFromLambda,

        // Samples showing how to create, import and add a kernel plugin and invoke its functions in AOT applications.
        KernelPluginSamples.CreatePluginFromType,
        KernelPluginSamples.ImportPluginFromType,
        KernelPluginSamples.AddPluginFromType,

        // Samples showing how to use ONNX chat completion service in AOT applications.
        OnnxChatCompletionSamples.GetChatMessageContent,
        OnnxChatCompletionSamples.GetStreamingChatMessageContents
    ];

    private static readonly Func<IConfigurationRoot, Task>[] s_tests =
    [
        // Tests for functions
        KernelFunctionFactoryTests.CreateFromLambda,
        KernelFunctionFactoryTests.CreateFromMethod,
        KernelFunctionFactoryTests.CreateFromStringPrompt,
        KernelFunctionFactoryTests.CreateFromPromptTemplate,

        KernelExtensions_KernelFunctionTests.CreateFromLambda,
        KernelExtensions_KernelFunctionTests.CreateFromMethod,
        KernelExtensions_KernelFunctionTests.CreateFromStringPrompt,
        KernelExtensions_KernelFunctionTests.CreateFromPromptTemplate,

        KernelExtensions_InvokePromptTests.InvokePromptAsync,
        KernelExtensions_InvokePromptTests.InvokePromptStreamingAsync,

        // Tests for plugins
        KernelPluginFactoryTests.CreateFromType,
        KernelPluginFactoryTests.CreateFromObject,

        KernelExtensions_KernelPluginTests.CreateFromType,
        KernelExtensions_KernelPluginTests.CreateFromObject,
        KernelExtensions_KernelPluginTests.ImportFromType,
        KernelExtensions_KernelPluginTests.ImportFromObject,

        KernelPluginExtensionsTests.AddFromType,
        KernelPluginExtensionsTests.AddFromObject,

        KernelBuilderPluginsExtensionsTests.AddFromType,
        KernelBuilderPluginsExtensionsTests.AddFromObject,
    ];

    private static async Task<bool> RunAsync(IEnumerable<Func<IConfigurationRoot, Task>> functionsToRun, IConfigurationRoot config)
    {
        bool failed = false;

        foreach (var function in functionsToRun)
        {
            Console.Write($"Running - {function.Method.DeclaringType?.Name}.{function.Method.Name}");

            try
            {
                await function(config);

                Console.WriteLine(" - Success");
            }
            catch (Exception ex)
            {
                failed = true;
                Console.WriteLine($" - Fail: {ex.Message}");
            }
        }

        return failed;
    }
}
