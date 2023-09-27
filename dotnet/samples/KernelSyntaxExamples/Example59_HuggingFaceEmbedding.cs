// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Security.Authentication;
using System.Security.Cryptography.X509Certificates;
using System.Text;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel;

public static class Example59_HuggingFaceEmbedding
{
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Example59_HuggingFaceEmbedding ========");


        IKernel kernel = Kernel.Builder
                .WithHuggingFaceTextEmbeddingGenerationService("sentence-transformers/all-MiniLM-L6-v2", "https://api-inference.huggingface.co/pipeline/feature-extraction")

      .Build();
        var embedinggenerator = kernel.GetService<ITextEmbeddingGeneration>();
        var embeding = await embedinggenerator.GenerateEmbeddingAsync("british short hair");

    }
}
