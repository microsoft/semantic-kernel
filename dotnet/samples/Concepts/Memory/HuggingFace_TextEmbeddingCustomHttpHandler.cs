// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel.Connectors.HuggingFace;
using Microsoft.SemanticKernel.Connectors.Sqlite;
using Microsoft.SemanticKernel.Memory;

#pragma warning disable CS8602 // Dereference of a possibly null reference.

namespace Memory;

/// <summary>
/// This example shows how to use custom <see cref="HttpClientHandler"/> to override Hugging Face HTTP response.
/// Generally, an embedding model will return results as a 1 * n matrix for input type [string]. However, the model can have different matrix dimensionality.
/// For example, the <a href="https://huggingface.co/cointegrated/LaBSE-en-ru">cointegrated/LaBSE-en-ru</a> model returns results as a 1 * 1 * 4 * 768 matrix, which is different from Hugging Face embedding generation service implementation.
/// To address this, a custom <see cref="HttpClientHandler"/> can be used to modify the response before sending it back.
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted")]
public class HuggingFace_TextEmbeddingCustomHttpHandler(ITestOutputHelper output) : BaseTest(output)
{
    public async Task RunInferenceApiEmbeddingCustomHttpHandlerAsync()
    {
        Console.WriteLine("\n======= Hugging Face Inference API - Embedding Example ========\n");

        var hf = new HuggingFaceTextEmbeddingGenerationService(
            "cointegrated/LaBSE-en-ru",
            apiKey: TestConfiguration.HuggingFace.ApiKey,
            httpClient: new HttpClient(new CustomHttpClientHandler()
            {
                CheckCertificateRevocationList = true
            })
        );

        var sqliteMemory = await SqliteMemoryStore.ConnectAsync("./../../../Sqlite.sqlite");

        var skMemory = new MemoryBuilder()
            .WithTextEmbeddingGeneration(hf)
            .WithMemoryStore(sqliteMemory)
            .Build();

        await skMemory.SaveInformationAsync("Test", "THIS IS A SAMPLE", "sample", "TEXT");
    }

    private sealed class CustomHttpClientHandler : HttpClientHandler
    {
        private readonly JsonSerializerOptions _jsonOptions = new();
        protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            // Log the request URI
            //Console.WriteLine($"Request: {request.Method} {request.RequestUri}");

            // Send the request and get the response
            HttpResponseMessage response = await base.SendAsync(request, cancellationToken);

            // Log the response status code
            //Console.WriteLine($"Response: {(int)response.StatusCode} {response.ReasonPhrase}");

            // You can manipulate the response here
            // For example, add a custom header
            // response.Headers.Add("X-Custom-Header", "CustomValue");

            // For example, modify the response content
            Stream originalContent = await response.Content.ReadAsStreamAsync(cancellationToken).ConfigureAwait(false);
            List<List<List<ReadOnlyMemory<float>>>> modifiedContent = (await JsonSerializer.DeserializeAsync<List<List<List<ReadOnlyMemory<float>>>>>(originalContent, _jsonOptions, cancellationToken).ConfigureAwait(false))!;

            Stream modifiedStream = new MemoryStream();
            await JsonSerializer.SerializeAsync(modifiedStream, modifiedContent[0][0].ToList(), _jsonOptions, cancellationToken).ConfigureAwait(false);
            response.Content = new StreamContent(modifiedStream);

            // Return the modified response
            return response;
        }
    }
}
