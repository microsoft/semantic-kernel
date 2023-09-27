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

        var CERT_PATH = "C:\\Users\\Ashish.Shiwalkar\\AppData\\Roaming\\ZscalerRootCA.cer";
        var handler = new HttpClientHandler();
        handler.ClientCertificateOptions = ClientCertificateOption.Manual;
        handler.SslProtocols = SslProtocols.Tls12;
        handler.ClientCertificates.Add(new X509Certificate2(CERT_PATH));
        var client = new HttpClient(handler);
        client.BaseAddress = new Uri("https://api-inference.huggingface.co/pipeline/feature-extraction");

        IKernel kernel = Kernel.Builder
                .WithHuggingFaceTextEmbeddingGenerationService("sentence-transformers/all-MiniLM-L6-v2", httpClient: client)

      .Build();
        var embedinggenerator = kernel.GetService<ITextEmbeddingGeneration>();
        var embeding = await embedinggenerator.GenerateEmbeddingAsync("british short hair");

    }
}
