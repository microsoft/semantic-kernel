// Copyright (c) Microsoft. All rights reserved.

using SemanticKernel.AotTests.UnitTests;

namespace SemanticKernel.AotTests;

/// <summary>
/// This application is created in accordance with the instructions in the blog post at https://devblogs.microsoft.com/dotnet/creating-aot-compatible-libraries to ensure that
/// all Native-AOT-related warnings missed by the Roslyn analyzers are caught by the AOT compiler used in this application.
/// </summary>
internal sealed class Program
{
    private static async Task<int> Main(string[] args)
    {
        bool success = await RunUnitTestsAsync(s_unitTests);

        return success ? 1 : 0;
    }

    private static readonly Func<Task>[] s_unitTests =
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

    private static async Task<bool> RunUnitTestsAsync(IEnumerable<Func<Task>> functionsToRun)
    {
        bool failed = false;

        foreach (var function in functionsToRun)
        {
            Console.Write($"Running - {function.Method.DeclaringType?.Name}.{function.Method.Name}");

            try
            {
                await function.Invoke();

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
