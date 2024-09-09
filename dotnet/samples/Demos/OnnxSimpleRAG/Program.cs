// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable SKEXP0070
#pragma warning disable SKEXP0050
#pragma warning disable SKEXP0001

using System;
using System.IO;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Plugins.Memory;

// Ensure you follow the preparation steps provided in the README.md
var config = new ConfigurationBuilder().AddUserSecrets<Program>().Build();

// Path to the folder of your downloaded ONNX PHI-3 model
var chatModelPath = config["Onnx:ModelPath"]!;
var chatModelId = config["Onnx:ModelId"] ?? "phi-3";

// Path to the file of your downloaded ONNX BGE-MICRO-V2 model
var embeddingModelPath = config["Onnx:EmbeddingModelPath"]!;

// Path to the vocab file your ONNX BGE-MICRO-V2 model
var embeddingVocabPath = config["Onnx:EmbeddingVocabPath"]!;

// Load the services
var builder = Kernel.CreateBuilder()
    .AddOnnxRuntimeGenAIChatCompletion(chatModelId, chatModelPath)
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
foreach (var factTextFile in Directory.GetFiles("Facts", "*.txt"))
{
    var factContent = File.ReadAllText(factTextFile);
    await semanticTextMemory.SaveInformationAsync(
        collection: collectionName,
        text: factContent,
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
