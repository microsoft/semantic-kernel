// Copyright (c) Microsoft. All rights reserved.

using System.Globalization;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;

namespace GettingStarted;

public sealed class Step8_Pipelining(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Provides an example of combining multiple functions into a single function that invokes
    /// them in a sequence, passing the output from one as input to the next.
    /// </summary>
    [Fact]
    public async Task CreateFunctionPipeline()
    {
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.AddOpenAIChatCompletion(
            TestConfiguration.OpenAI.ChatModelId,
            TestConfiguration.OpenAI.ApiKey);
        builder.Services.AddLogging(c => c.AddConsole().SetMinimumLevel(LogLevel.Trace));
        Kernel kernel = builder.Build();

        Console.WriteLine("================ PIPELINE ================");
        {
            // Create a pipeline of functions that will parse a string into a double, multiply it by a double, truncate it to an int, and then humanize it.
            KernelFunction parseDouble = KernelFunctionFactory.CreateFromMethod((string s) => double.Parse(s, CultureInfo.InvariantCulture), "parseDouble");
            KernelFunction multiplyByN = KernelFunctionFactory.CreateFromMethod((double i, double n) => i * n, "multiplyByN");
            KernelFunction truncate = KernelFunctionFactory.CreateFromMethod((double d) => (int)d, "truncate");
            KernelFunction humanize = KernelFunctionFactory.CreateFromPrompt(new PromptTemplateConfig()
            {
                Template = "Spell out this number in English: {{$number}}",
                InputVariables = [new() { Name = "number" }],
            });
            KernelFunction pipeline = KernelFunctionCombinators.Pipe([parseDouble, multiplyByN, truncate, humanize], "pipeline");

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

        Console.WriteLine("================ GRAPH ================");
        {
            KernelFunction rand = KernelFunctionFactory.CreateFromMethod(() => Random.Shared.Next(), "GetRandomInt32");
            KernelFunction mult = KernelFunctionFactory.CreateFromMethod((int i, int j) => i * j, "Multiply");

            // - Invokes rand and stores the random number into args["i"]
            // - Invokes rand and stores the random number into args["j"]
            // - Multiplies arg["i"] and args["j"] to produce the final result
            KernelFunction graph = KernelFunctionCombinators.Pipe(new[]
            {
                (rand, "i"),
                (rand, "j"),
                (mult, "")
            }, "graph");

            Console.WriteLine(await graph.InvokeAsync(kernel));
        }
    }
}

public static class KernelFunctionCombinators
{
    /// <summary>
    /// Invokes a pipeline of functions, running each in order and passing the output from one as the first argument to the next.
    /// </summary>
    /// <param name="functions">The pipeline of functions to invoke.</param>
    /// <param name="kernel">The kernel to use for the operations.</param>
    /// <param name="arguments">The arguments.</param>
    /// <param name="cancellationToken">The cancellation token to monitor for a cancellation request.</param>
    public static Task<FunctionResult> InvokePipelineAsync(
        IEnumerable<KernelFunction> functions, Kernel kernel, KernelArguments arguments, CancellationToken cancellationToken) =>
        Pipe(functions).InvokeAsync(kernel, arguments, cancellationToken);

    /// <summary>
    /// Invokes a pipeline of functions, running each in order and passing the output from one as the named argument to the next.
    /// </summary>
    /// <param name="functions">The sequence of functions to invoke, along with the name of the argument to assign to the result of the function's invocation.</param>
    /// <param name="kernel">The kernel to use for the operations.</param>
    /// <param name="arguments">The arguments.</param>
    /// <param name="cancellationToken">The cancellation token to monitor for a cancellation request.</param>
    public static Task<FunctionResult> InvokePipelineAsync(
        IEnumerable<(KernelFunction Function, string OutputVariable)> functions, Kernel kernel, KernelArguments arguments, CancellationToken cancellationToken) =>
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

        KernelFunction[] funcs = functions.ToArray();
        Array.ForEach(funcs, f => ArgumentNullException.ThrowIfNull(f));

        var funcsAndVars = new (KernelFunction Function, string OutputVariable)[funcs.Length];
        for (int i = 0; i < funcs.Length; i++)
        {
            string p = "";
            if (i < funcs.Length - 1)
            {
                var parameters = funcs[i + 1].Metadata.Parameters;
                if (parameters.Count > 0)
                {
                    p = parameters[0].Name;
                }
            }

            funcsAndVars[i] = (funcs[i], p);
        }

        return Pipe(funcsAndVars, functionName, description);
    }

    /// <summary>
    /// Creates a function whose invocation will invoke each of the supplied functions in sequence.
    /// </summary>
    /// <param name="functions">The pipeline of functions to invoke, along with the name of the argument to assign to the result of the function's invocation.</param>
    /// <param name="functionName">The name of the combined operation.</param>
    /// <param name="description">The description of the combined operation.</param>
    /// <returns>The result of the final function.</returns>
    /// <remarks>
    /// The result from one function will be fed into the first argument of the next function.
    /// </remarks>
    public static KernelFunction Pipe(
        IEnumerable<(KernelFunction Function, string OutputVariable)> functions,
        string? functionName = null,
        string? description = null)
    {
        ArgumentNullException.ThrowIfNull(functions);

        (KernelFunction Function, string OutputVariable)[] arr = functions.ToArray();
        Array.ForEach(arr, f =>
        {
            ArgumentNullException.ThrowIfNull(f.Function);
            ArgumentNullException.ThrowIfNull(f.OutputVariable);
        });

        return KernelFunctionFactory.CreateFromMethod(async (Kernel kernel, KernelArguments arguments) =>
        {
            FunctionResult? result = null;
            for (int i = 0; i < arr.Length; i++)
            {
                result = await arr[i].Function.InvokeAsync(kernel, arguments).ConfigureAwait(false);
                if (i < arr.Length - 1)
                {
                    arguments[arr[i].OutputVariable] = result.GetValue<object>();
                }
            }

            return result;
        }, functionName, description);
    }
}
