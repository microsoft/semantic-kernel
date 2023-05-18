// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AI.HuggingFace.TextCompletion;
using RepoUtils;

/**
 * The following example shows how to use Semantic Kernel with HuggingFace API.
 */

// ReSharper disable once InconsistentNaming
public static class Example20_HuggingFace
{
    public static async Task RunAsync()
    {
        Console.WriteLine("======== HuggingFace text completion AI ========");

        IKernel kernel = new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();

        // Add HuggingFace text completion service
        kernel.Config.AddTextCompletionService(_ => new HuggingFaceTextCompletion(Env.Var("HF_API_KEY"), model: "gpt2"));

        const string FunctionDefinition = "Question: {{$input}}; Answer:";

        var questionAnswerFunction = kernel.CreateSemanticFunction(FunctionDefinition);

        var result = await questionAnswerFunction.InvokeAsync("What is New York?");

        Console.WriteLine(result);
    }
}
