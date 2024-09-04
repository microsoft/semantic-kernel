// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable SKEXP0070
#pragma warning disable SKEXP0050
#pragma warning disable SKEXP0001

using System;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Plugins.Memory;

// Ensure you follow the preparation steps provided in the README.md

// Path to the folder of your downloaded ONNX PHI-3 model
var chatModelPath = @"C:\path\to\huggingface\Phi-3-mini-4k-instruct-onnx\cpu_and_mobile\cpu-int4-rtn-block-32";

// Path to the file of your downloaded ONNX BGE-MICRO-V2 model
var embeddingModelPath = @"C:\path\to\huggingface\bge-micro-v2\onnx\model.onnx";

// Path to the vocab file your ONNX BGE-MICRO-V2 model
var embeddingVocabPath = @"C:\path\to\huggingface\bge-micro-v2\vocab.txt";

// Load the services
var builder = Kernel.CreateBuilder()
    .AddOnnxRuntimeGenAIChatCompletion("phi-3", chatModelPath)
    .AddBertOnnxTextEmbeddingGeneration(embeddingModelPath, embeddingVocabPath);

// Build Kernel
var kernel = builder.Build();

// Get the instances of the services
var chatService = kernel.GetRequiredService<IChatCompletionService>();
var embeddingService = kernel.GetRequiredService<ITextEmbeddingGenerationService>();

// Create a memory store and a semantic text memory
var memoryStore = new VolatileMemoryStore();
var semanticTextMemory = new SemanticTextMemory(memoryStore, embeddingService);

// Loading it for Save, Recall and other methods
kernel.ImportPluginFromObject(new TextMemoryPlugin(semanticTextMemory));

// Save some information to the memory
var collectionName = "ExampleCollection";
foreach (var fact in new[] {
    "Semantic Kernel is a lightweight, open-source development kit that lets you easily build AI agents and integrate the latest AI models into your C#, Python, or Java codebase. It serves as an efficient middleware that enables rapid delivery of enterprise-grade solutions.",
    "Kernel Memory (KM) is a multi-modal AI Service specialized in the efficient indexing of datasets through custom continuous data hybrid pipelines, with support for Retrieval Augmented Generation (RAG), synthetic memory, prompt engineering, and custom semantic memory processing." })
{
    await semanticTextMemory.SaveInformationAsync(
        collection: collectionName,
        text: fact,
        id: Guid.NewGuid().ToString());
}

// Start the conversation
while (true)
{
    // Get user input
    Console.ForegroundColor = ConsoleColor.White;
    Console.Write("User > ");
    var question = Console.ReadLine()!;

    if (question is null || string.IsNullOrWhiteSpace(question))
    {
        // Exit the demo if the user input is null or empty
        return;
    }

    // Invoke the kernel with the user input
    var response = kernel.InvokePromptStreamingAsync(
        promptTemplate: @"Question: {{$input}}
        Answer the question using the memory content: {{Recall}}",
        arguments: new KernelArguments()
        {
            { "input", question },
            { "collection", collectionName }
        });

    Console.Write("\nAssistant > ");

    await foreach (var message in response)
    {
        Console.Write(message);
    }

    Console.WriteLine();
}
