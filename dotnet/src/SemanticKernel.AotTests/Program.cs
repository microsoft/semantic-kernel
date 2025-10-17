// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using SemanticKernel.AotTests.UnitTests.Core.Functions;
using SemanticKernel.AotTests.UnitTests.Core.Plugins;
using SemanticKernel.AotTests.UnitTests.Search;

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

    [UnconditionalSuppressMessage("AOT", "IL3050:Calling members annotated with 'RequiresDynamicCodeAttribute' may break functionality when AOT compiling.", Justification = "Test application intentionally tests dynamic code paths. VectorStoreTextSearch LINQ filtering requires reflection for dynamic expression building from runtime filter specifications.")]
    private static readonly Func<Task>[] s_unitTests =
    [
        // Tests for functions
        KernelFunctionFromMethodTests.CreateUsingOverloadWithFunctionDetails,
        KernelFunctionFromMethodTests.CreateUsingOverloadWithOptions,
        KernelFunctionFromMethodTests.CreateMetadataUsingOverloadWithFunctionDetails,
        KernelFunctionFromMethodTests.CreateMetadataUsingOverloadWithOptions,

        KernelFunctionFactoryTests.CreateFromLambda,
        KernelFunctionFactoryTests.CreateFromMethod,
        KernelFunctionFactoryTests.CreateFromStringPrompt,
        KernelFunctionFactoryTests.CreateFromPromptTemplate,

        KernelExtensions_KernelFunctionTests.CreateFromLambda,
        KernelExtensions_KernelFunctionTests.CreateFromMethod,
        KernelExtensions_KernelFunctionTests.CreateFromStringPrompt,
        KernelExtensions_KernelFunctionTests.CreateFromPromptTemplate,

        KernelExtensions_InvokePromptTests.InvokePrompt,
        KernelExtensions_InvokePromptTests.InvokePromptStreaming,

        KernelFunctionMetadataFactoryTests.CreateFromType,

        // Tests for plugins
        KernelPluginFactoryTests.CreateFromGenericParameterType,
        KernelPluginFactoryTests.CreateFromObject,

        KernelExtensions_KernelPluginTests.CreateFromType,
        KernelExtensions_KernelPluginTests.CreateFromObject,
        KernelExtensions_KernelPluginTests.ImportFromType,
        KernelExtensions_KernelPluginTests.ImportFromObject,

        KernelPluginExtensionsTests.AddFromType,
        KernelPluginExtensionsTests.AddFromObject,

        KernelBuilderPluginsExtensionsTests.AddFromType,
        KernelBuilderPluginsExtensionsTests.AddFromObject,

        // Tests for text search
        VectorStoreTextSearchTests.GetTextSearchResultsAsync,
        VectorStoreTextSearchTests.AddVectorStoreTextSearch,

        TextSearchExtensionsTests.CreateWithSearch,
        TextSearchExtensionsTests.CreateWithGetTextSearchResults,
        TextSearchExtensionsTests.CreateWithGetSearchResults,
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
