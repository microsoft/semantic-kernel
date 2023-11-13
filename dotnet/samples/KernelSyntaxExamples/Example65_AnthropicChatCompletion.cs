// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;

// Example usage of Anthropic's chat completion service.
// ReSharper disable once InconsistentNaming
public static class Example65_AnthropicChatCompletion
{
    public static async Task RunAsync()
    {
        Console.WriteLine("=== Example with Anthropic Chat Completion ===");

        var cfg = TestConfiguration.Anthropic;

        var kernel = new KernelBuilder()
            .WithAnthropicChatCompletionService(cfg.ModelId, cfg.ApiKey, cfg.ServiceId, true, true)
            .Build();

        var semanticFunction = kernel.CreateSemanticFunction("{{$input}}");
        var ask = "In the classic Star Wars films, who was Luke Skywalker's father?";

        var response = await kernel.RunAsync(ask, semanticFunction);

        Console.WriteLine($"Ask: {ask}");
        Console.WriteLine($"Response: {response}");
    }
}