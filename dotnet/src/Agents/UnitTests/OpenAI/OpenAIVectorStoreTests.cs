// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.OpenAI;
using OpenAI.VectorStores;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI;

/// <summary>
/// Unit testing of <see cref="OpenAIVectorStore"/>.
/// </summary>
public sealed class OpenAIVectorStoreTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;

    /// <summary>
    /// %%%
    /// </summary>
    [Fact]
    public void VerifyOpenAIVectorStoreInitialization()
    {
        OpenAIVectorStore store = new("#vs1", this.CreateTestConfiguration());
        Assert.Equal("#vs1", store.VectorStoreId);
    }

    /// <summary>
    /// %%%
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIVectorStoreDeleteAsync()
    {
        this.SetupResponse(HttpStatusCode.OK, ResponseContent.DeleteStore);

        OpenAIVectorStore store = new("#vs1", this.CreateTestConfiguration());
        bool isDeleted = await store.DeleteAsync();

        Assert.True(isDeleted);
    }

    /// <summary>
    /// %%%
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIVectorStoreListAsync()
    {
        this.SetupResponse(HttpStatusCode.OK, ResponseContent.ListStores);

        VectorStore[] stores = await OpenAIVectorStore.GetVectorStoresAsync(this.CreateTestConfiguration()).ToArrayAsync();

        Assert.Equal(2, stores.Length);
    }

    /// <summary>
    /// %%%
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIVectorStoreAddFileAsync()
    {
        this.SetupResponse(HttpStatusCode.OK, ResponseContent.AddFile);

        OpenAIVectorStore store = new("#vs1", this.CreateTestConfiguration());
        await store.AddFileAsync("#file_1");

        // %%% VERIFY
    }

    /// <summary>
    /// %%%
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIVectorStoreRemoveFileAsync()
    {
        this.SetupResponse(HttpStatusCode.OK, ResponseContent.DeleteFile);

        OpenAIVectorStore store = new("#vs1", this.CreateTestConfiguration());
        bool isDeleted = await store.RemoveFileAsync("#file_1");

        Assert.True(isDeleted);
    }

    /// <summary>
    /// %%%
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIVectorStoreGetFilesAsync()
    {
        this.SetupResponse(HttpStatusCode.OK, ResponseContent.ListFiles);

        OpenAIVectorStore store = new("#vs1", this.CreateTestConfiguration());
        string[] files = await store.GetFilesAsync().ToArrayAsync();

        Assert.Equal(2, files.Length);
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
    public OpenAIVectorStoreTests()
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
        public const string AddFile =
            """
            {
              "id": "#file_1",
              "object": "vector_store.file",
              "created_at": 1699061776,
              "usage_bytes": 1234,
              "vector_store_id": "vs_abcd",
              "status": "completed",
              "last_error": null
            }
            """;

        public const string DeleteFile =
            """
            {
              "id": "#file_1",
              "object": "vector_store.file.deleted",
              "deleted": true
            }
            """;

        public const string DeleteStore =
            """
            {
              "id": "vs_abc123",
              "object": "vector_store.deleted",
              "deleted": true
            }
            """;

        public const string ListFiles =
            """
            {
              "object": "list",
              "data": [
                {
                  "id": "file-abc123",
                  "object": "vector_store.file",
                  "created_at": 1699061776,
                  "vector_store_id": "vs_abc123"
                },
                {
                  "id": "file-abc456",
                  "object": "vector_store.file",
                  "created_at": 1699061776,
                  "vector_store_id": "vs_abc123"
                }
              ],
              "first_id": "file-abc123",
              "last_id": "file-abc456",
              "has_more": false
            }            
            """;

        public const string ListStores =
            """
            {
              "object": "list",
              "data": [
                {
                  "id": "vs_abc123",
                  "object": "vector_store",
                  "created_at": 1699061776,
                  "name": "Support FAQ",
                  "bytes": 139920,
                  "file_counts": {
                    "in_progress": 0,
                    "completed": 3,
                    "failed": 0,
                    "cancelled": 0,
                    "total": 3
                  }
                },
                {
                  "id": "vs_abc456",
                  "object": "vector_store",
                  "created_at": 1699061776,
                  "name": "Support FAQ v2",
                  "bytes": 139920,
                  "file_counts": {
                    "in_progress": 0,
                    "completed": 3,
                    "failed": 0,
                    "cancelled": 0,
                    "total": 3
                  }
                }
              ],
              "first_id": "vs_abc123",
              "last_id": "vs_abc456",
              "has_more": false
            }            
            """;
    }
}
