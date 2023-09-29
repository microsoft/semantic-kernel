// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel;

public static class Example60_HuggingFaceEmbedding
{
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Example59_HuggingFaceEmbedding ========");


        IKernel kernel = Kernel.Builder
                .WithHuggingFaceTextEmbeddingGenerationService("sentence-transformers/all-MiniLM-L6-v2",
                "https://api-inference.huggingface.co/pipeline/feature-extraction",
                serviceId: "all-MiniLM-L6-v2")
                 .WithHuggingFaceTextEmbeddingGenerationService("flax-sentence-embeddings/st-codesearch-distilroberta-base",
                "https://api-inference.huggingface.co/pipeline/feature-extraction",
                serviceId: "distilroberta")
      .Build();


        var embedinGgeneratorMiniLM = kernel.GetService<ITextEmbeddingGeneration>("all-MiniLM-L6-v2");
        var embedingMiniLM = await embedinGgeneratorMiniLM.GenerateEmbeddingAsync("british short hair");

        var embedinGeneratorDistilRoberta = kernel.GetService<ITextEmbeddingGeneration>("distilroberta");
        var embedinDistilRoberta = await embedinGeneratorDistilRoberta.GenerateEmbeddingAsync("british short hair");

        Console.WriteLine("======== Embedding all-MiniLM-L6-v2 ========");
        Console.Write("[");
        foreach (var item in embedingMiniLM.ToArray())
        {
            Console.Write(item);
        }
        Console.Write("]");

        Console.WriteLine(" ");
        Console.WriteLine(" ");


        Console.WriteLine("======== Embedding google_speech_command_xvector ========");
        Console.Write("[");
        foreach (var item in embedinDistilRoberta.ToArray())
        {
            Console.Write(item);
        }
        Console.Write("]");

    }
}
