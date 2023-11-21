using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.Embeddings;

public static class Example72_HuggingFaceEncoding
{
    const string SentenceTransformerModelId = "sentence-transformers/all-MiniLM-L6-v2";
    const string SentenceTransformerEndpoint = "https://api-inference.huggingface.co/pipeline/feature-extraction";    

    public static async Task RunAsync()
    {
        Console.WriteLine($"======== {nameof(Example72_HuggingFaceEncoding)} ========");

        if (TestConfiguration.HuggingFace.ApiKey == null)
        {
            Console.WriteLine("HuggingFace apiKey not found. Skipping example.");
            return;
        }
       

        var kernel = new KernelBuilder()            
                .WithHuggingFaceTextEmbeddingGenerationService(
                    SentenceTransformerModelId,
                    SentenceTransformerEndpoint)
                //.WithOpenAITextEmbeddingGenerationService(
                //    apiKey: TestConfiguration.OpenAI.ApiKey, 
                //    modelId: TestConfiguration.OpenAI.EmbeddingModelId)
                .Build();

        var embeddingGenerator = kernel.GetService<ITextEmbeddingGeneration>();
        var embedding = await embeddingGenerator.GenerateEmbeddingAsync("Hello world");

        Console.WriteLine($"Embedding: {string.Join(", ", embedding)}");
    }
}
