// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Net;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.OpenAI;
using OpenAI.VectorStores;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI;

/// <summary>
/// Unit testing of <see cref="OpenAIVectorStoreBuilder"/>.
/// </summary>
public sealed class OpenAIVectorStoreBuilderTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;

    /// <summary>
    /// %%%
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIVectorStoreBuilderEmptyAsync()
    {
        this.SetupResponse(HttpStatusCode.OK, ResponseContent.CreateStore);

        VectorStore store =
            await new OpenAIVectorStoreBuilder(this.CreateTestConfiguration())
                .CreateAsync();

        Assert.NotNull(store);
    }

    /// <summary>
    /// %%%
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIVectorStoreBuilderFluentAsync()
    {
        this.SetupResponse(HttpStatusCode.OK, ResponseContent.CreateStore);

        Dictionary<string, string> metadata = new() { { "key2", "value2" } };

        VectorStore store =
            await new OpenAIVectorStoreBuilder(this.CreateTestConfiguration())
                .WithName("my_vector_store")
                .AddFile("#file_1")
                .AddFiles(["#file_2", "#file_3"])
                .AddFiles(["#file_4", "#file_5"])
                .WithChunkingStrategy(1000, 400)
                .WithExpiration(TimeSpan.FromDays(30))
                .WithMetadata("key1", "value1")
                .WithMetadata(metadata)
                .CreateAsync();

        Assert.NotNull(store);
    }

    /// <inheritdoc/>
    public void Dispose()
    {
        this._messageHandlerStub.Dispose();
        this._httpClient.Dispose();
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIAssistantAgentTests"/> class.
    /// </summary>
    public OpenAIVectorStoreBuilderTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub, disposeHandler: false);
    }

    private OpenAIServiceConfiguration CreateTestConfiguration(bool targetAzure = false)
        => targetAzure ?
            OpenAIServiceConfiguration.ForAzureOpenAI(apiKey: "fakekey", endpoint: new Uri("https://localhost"), this._httpClient) :
            OpenAIServiceConfiguration.ForOpenAI(apiKey: "fakekey", endpoint: null, this._httpClient);

    private void SetupResponse(HttpStatusCode statusCode, string content)
    {
        this._messageHandlerStub.ResponseToReturn =
            new(statusCode)
            {
                Content = new StringContent(content)
            };
    }

    private void SetupResponses(HttpStatusCode statusCode, params string[] content)
    {
        foreach (var item in content)
        {
#pragma warning disable CA2000 // Dispose objects before losing scope
            this._messageHandlerStub.ResponseQueue.Enqueue(
                new(statusCode)
                {
                    Content = new StringContent(item)
                });
#pragma warning restore CA2000 // Dispose objects before losing scope
        }
    }

    private static class ResponseContent
    {
        public const string CreateStore =
            """
            {
              "id": "vs_123",
              "object": "vector_store",
              "created_at": 1698107661,
              "usage_bytes": 123456,
              "last_active_at": 1698107661,
              "name": "my_vector_store",
              "status": "completed",
              "file_counts": {
                "in_progress": 0,
                "completed": 5,
                "cancelled": 0,
                "failed": 0,
                "total": 5
              },
              "metadata": {},
              "last_used_at": 1698107661
            }
            """;
    }
}
