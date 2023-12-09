// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;

#pragma warning disable RCS1110 // Declare type inside namespace.
#pragma warning disable CA5394

public static class Example74_Pipelining
{
    /// <summary>
    /// Provides an example of combining multiple functions into a single function that invokes
    /// them in a sequence, passing the output from one as input to the next.
    /// </summary>
    public static async Task RunAsync()
    {
        // Create a pipeline of functions that will parse a string into an int, multiply it by a double, truncate it to an int, and then humanize it.
        KernelFunction parseInt32 = KernelFunctionFactory.CreateFromMethod((string s) => double.Parse(s, CultureInfo.InvariantCulture), "parseInt32");
        KernelFunction multiplyByN = KernelFunctionFactory.CreateFromMethod((double i, double n) => i * n, "multiplyByN");
        KernelFunction truncate = KernelFunctionFactory.CreateFromMethod((double d) => (int)d, "truncate");
        KernelFunction humanize = KernelFunctionFactory.CreateFromPrompt(new PromptTemplateConfig()
        {
            Template = "Spell out this number in English: {{$number}}",
            InputVariables = new() { new() { Name = "number" } },
        });
        KernelFunction pipeline = KernelFunctionCombinators.Pipe(new[] { parseInt32, multiplyByN, truncate, humanize }, "pipeline");

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.AddOpenAIChatCompletion(
            TestConfiguration.OpenAI.ChatModelId,
            TestConfiguration.OpenAI.ApiKey);
        builder.Services.AddLogging(c => c.AddConsole().SetMinimumLevel(LogLevel.Trace));
        Kernel kernel = builder.Build();

        KernelArguments args = new()
        {
            ["s"] = "123.456",
            ["n"] = (double)78.90,
        };

        // - The parseInt32 function will be invoked, read "123.456" from the arguments, and parse it into (double)123.456.
        // - The multiplyByN function will be invoked, with i=123.456 and n=78.90, and return (double)9740.6784.
        // - The truncate function will be invoked, with d=9740.6784, and return (int)9740, which will be the final result.
        Console.WriteLine(await pipeline.InvokeAsync(kernel, args));
    }
}

public static class KernelFunctionCombinators
{
    /// <summary>
    /// Invokes a pipeline of functions, running each in order and passing the output from one as the first argument to the next.
    /// </summary>
    /// <param name="functions">The functions to invoke.</param>
    /// <param name="kernel">The kernel to use for the operations.</param>
    /// <param name="arguments">The arguments.</param>
    /// <param name="cancellationToken">The cancellation token to monitor for a cancellation request.</param>
    /// <returns></returns>
    public static Task<FunctionResult> InvokePipelineAsync(
        IEnumerable<KernelFunction> functions, Kernel kernel, KernelArguments arguments, CancellationToken cancellationToken) =>
        Pipe(functions).InvokeAsync(kernel, arguments, cancellationToken);

    /// <summary>
    /// Creates a function whose invocation will invoke each of the supplied functions in sequence.
    /// </summary>
    /// <param name="functions">The pipeline of functions to invoke.</param>
    /// <param name="functionName">The name of the combined operation.</param>
    /// <param name="description">The description of the combined operation.</param>
    /// <returns>The result of the final function.</returns>
    /// <remarks>
    /// The result from one function will be fed into the first argument of the next function.
    /// </remarks>
    public static KernelFunction Pipe(
        IEnumerable<KernelFunction> functions,
        string? functionName = null,
        string? description = null)
    {
        ArgumentNullException.ThrowIfNull(functions);

        KernelFunction[] arr = functions.ToArray();
        Array.ForEach(arr, f => ArgumentNullException.ThrowIfNull(f));

        return KernelFunctionFactory.CreateFromMethod(async (Kernel kernel, KernelArguments arguments) =>
        {
            FunctionResult? result = null;
            for (int i = 0; i < arr.Length; i++)
            {
                result = await arr[i].InvokeAsync(kernel, arguments).ConfigureAwait(false);

                if (i < arr.Length - 1)
                {
                    if (arr[i + 1].Metadata.Parameters is { Count: > 0 } parameters)
                    {
                        arguments[parameters[0].Name] = result.GetValue<object>();
                    }
                }
            }

            return result;
        }, functionName, description);
    }
}
