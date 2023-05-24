// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.TextCompletion;
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

        IKernel kernel = new KernelBuilder()
            .WithLogger(ConsoleLogger.Log)
            // Add HuggingFace text completion service as a factory methods
            .WithDefaultAIService<ITextCompletion>((_) => new HuggingFaceTextCompletion(Env.Var("HF_API_KEY"), "gpt2"))
            .Build();

        const string FunctionDefinition = "Question: {{$input}}; Answer:";

        var questionAnswerFunction = kernel.CreateSemanticFunction(FunctionDefinition);

        var result = await questionAnswerFunction.InvokeAsync("What is New York?");

        Console.WriteLine(result);
    }
}
