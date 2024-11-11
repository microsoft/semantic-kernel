﻿// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable SKEXP0070
#pragma warning disable SKEXP0050
#pragma warning disable SKEXP0001
#pragma warning disable SKEXP0020

using System;
using System.IO;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.InMemory;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;

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

// Create a vector store and a collection to store information
var vectorStore = new InMemoryVectorStore();
var collection = vectorStore.GetCollection<string, InformationItem>("ExampleCollection");
await collection.CreateCollectionIfNotExistsAsync();

// Save some information to the memory
var collectionName = "ExampleCollection";
foreach (var factTextFile in Directory.GetFiles("Facts", "*.txt"))
{
    var factContent = File.ReadAllText(factTextFile);
    await collection.UpsertAsync(new()
    {
        Id = Guid.NewGuid().ToString(),
        Text = factContent,
        Embedding = await embeddingService.GenerateEmbeddingAsync(factContent)
    });
}

// Add a plugin to search the database with.
var vectorStoreTextSearch = new VectorStoreTextSearch<InformationItem>(collection, embeddingService);
kernel.Plugins.Add(vectorStoreTextSearch.CreateWithSearch("SearchPlugin"));

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

internal sealed class InformationItem
{
    [VectorStoreRecordKey]
    [TextSearchResultName]
    public string Id { get; set; } = string.Empty;

    [VectorStoreRecordData]
    [TextSearchResultValue]
    public string Text { get; set; } = string.Empty;

    [VectorStoreRecordVector(Dimensions: 384)]
    public ReadOnlyMemory<float> Embedding { get; set; }
}
