// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.HuggingFace;
using Microsoft.SemanticKernel.Connectors.Sqlite;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Memory;
using System.Text.Json;

namespace Memory;

/// <summary>
/// This sample provides an example of <see cref="HttpClientHandler"/> that will help you implement specific tasks.
///
/// In general, an embedding model will return results as a 1 * n matrix for input type [string]. However, it is possible for the model to have different matrix dimensionality. For example,
/// 
/// the <a href="https://huggingface.co/cointegrated/LaBSE-en-ru">cointegrated/LaBSE-en-ru</a> model returns results as a 1 * 1 * 4 * 768 matrix, which differs from what <see cref="SemanticTextMemory"/> expects from <see cref="EmbeddingGenerationExtensions"/>. 
/// To address this, a custom <see cref="HttpClientHandler"/> is created to modify the response before sending it back.
/// </summary>


public class MemoryHuggingFaceEmbedding_CustomHttpResponse(ITestOutputHelper output) : BaseTest(output)
{
    public async Task RunInferenceApiEmbeddingCustomHttpResponseAsync()
    {
        Console.WriteLine("\n======= Hugging Face Inference API - Embedding Example ========\n");

        var hf = new HuggingFaceTextEmbeddingGenerationService
        ("cointegrated/LaBSE-en-ru", apiKey: TestConfiguration.HuggingFace.ApiKey, httpClient:new HttpClient(new CustomHttpClientHandler()));

        var sqliteMemory = await SqliteMemoryStore.ConnectAsync("./../../../Sqlite.sqlite");

        var skMemory = new MemoryBuilder()
            .WithTextEmbeddingGeneration(hf)
            .WithMemoryStore(sqliteMemory)
            .Build();

        if (!await sqliteMemory.DoesCollectionExistAsync("Sqlite"))
        {
            await sqliteMemory.CreateCollectionAsync("Sqlite");
        }

        await skMemory.SaveInformationAsync("Test", "THIS IS A SAMPLE", "sample", "TEXT");
    }
}

public class CustomHttpClientHandler : HttpClientHandler
{
        protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            // Log the request URI
            Console.WriteLine($"Request: {request.Method} {request.RequestUri}");

            // Send the request and get the response
            HttpResponseMessage response = await base.SendAsync(request, cancellationToken);

            // Log the response status code
            Console.WriteLine($"Response: {(int)response.StatusCode} {response.ReasonPhrase}");

            // You can manipulate the response here
            // For example, add a custom header
            // response.Headers.Add("X-Custom-Header", "MyCustomValue");
            
            // For example, modify the response content
            string originalContent = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
            var modifiedContent = JsonSerializer.Deserialize<List<List<List<ReadOnlyMemory<float>>>>>(originalContent);
            var modifiedResponse = JsonSerializer.Serialize(modifiedContent[0][0].ToList());
            response.Content = new StringContent(modifiedResponse);

            // Return the modified response
            return response;
        }
}
