// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Linq;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.VectorData;
using Microsoft.ML.OnnxRuntimeGenAI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.InMemory;
using Microsoft.SemanticKernel.Connectors.Onnx;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;

Console.OutputEncoding = System.Text.Encoding.UTF8;

// Ensure you follow the preparation steps provided in the README.md
var config = new ConfigurationBuilder().AddUserSecrets<Program>().Build();

// Path to the folder of your downloaded ONNX PHI-3 model
var chatModelPath = config["Onnx:ModelPath"]!;
var chatModelId = config["Onnx:ModelId"] ?? "phi-3";

// Path to the file of your downloaded ONNX BGE-MICRO-V2 model
var embeddingModelPath = config["Onnx:EmbeddingModelPath"]!;

// Path to the vocab file your ONNX BGE-MICRO-V2 model
var embeddingVocabPath = config["Onnx:EmbeddingVocabPath"]!;

// If using Onnx GenAI 0.5.0 or later, the OgaHandle class must be used to track
// resources used by the Onnx services, before using any of the Onnx services.
using var ogaHandle = new OgaHandle();

// Load the services
var builder = Kernel.CreateBuilder()
    .AddOnnxRuntimeGenAIChatCompletion(chatModelId, chatModelPath)
    .AddBertOnnxEmbeddingGenerator(embeddingModelPath, embeddingVocabPath);

// Build Kernel
var kernel = builder.Build();

// Get the instances of the services
using var chatService = kernel.GetRequiredService<IChatCompletionService>() as OnnxRuntimeGenAIChatCompletionService;
var embeddingService = kernel.GetRequiredService<IEmbeddingGenerator<string, Embedding<float>>>();

// Create a vector store and a collection to store information
var vectorStore = new InMemoryVectorStore(new() { EmbeddingGenerator = embeddingService });
var collection = vectorStore.GetCollection<string, InformationItem>("ExampleCollection");
await collection.EnsureCollectionExistsAsync();

// Save some information to the memory
var collectionName = "ExampleCollection";
foreach (var factTextFile in Directory.GetFiles("Facts", "*.txt"))
{
    var factContent = File.ReadAllText(factTextFile);
    await collection.UpsertAsync(new InformationItem()
    {
        Id = Guid.NewGuid().ToString(),
        Text = factContent
    });
}

// Add a plugin to search the database with.
var vectorStoreTextSearch = new VectorStoreTextSearch<InformationItem>(collection);
kernel.Plugins.Add(vectorStoreTextSearch.CreateWithSearch("SearchPlugin"));

// Start the conversation
while (true)
{
    // Get user input
    Console.ForegroundColor = ConsoleColor.White;
    Console.Write("User > ");
    var question = Console.ReadLine()!;

    // Clean resources and exit the demo if the user input is null or empty
    if (question is null || string.IsNullOrWhiteSpace(question))
    {
        // To avoid any potential memory leak all disposable
        // services created by the kernel are disposed
        DisposeServices(kernel);
        return;
    }

    // Invoke the kernel with the user input
    var response = kernel.InvokePromptStreamingAsync(
        promptTemplate: @"Question: {{input}}
        Answer the question using the memory content:
        {{#with (SearchPlugin-Search input)}}
          {{#each this}}
            {{this}}
            -----------------
          {{/each}}
        {{/with}}",
        templateFormat: "handlebars",
        promptTemplateFactory: new HandlebarsPromptTemplateFactory(),
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

static void DisposeServices(Kernel kernel)
{
    foreach (var target in kernel
        .GetAllServices<IChatCompletionService>()
        .OfType<IDisposable>())
    {
        target.Dispose();
    }
}

/// <summary>
/// Information item to represent the embedding data stored in the memory
/// </summary>
internal sealed class InformationItem
{
    [VectorStoreKey]
    [TextSearchResultName]
    public string Id { get; set; } = string.Empty;

    [VectorStoreData]
    [TextSearchResultValue]
    public string Text { get; set; } = string.Empty;

    [VectorStoreVector(Dimensions: 384)]
    public string Embedding => this.Text;
}
