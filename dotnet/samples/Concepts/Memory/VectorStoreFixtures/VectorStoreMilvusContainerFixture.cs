// Copyright (c) Microsoft. All rights reserved.

using Docker.DotNet;
using Grpc.Core;
using Milvus.Client;

namespace Memory.VectorStoreFixtures;

/// <summary>
/// Fixture that starts a Milvus container for the samples and deletes it afterward.
/// </summary>
public class VectorStoreMilvusContainerFixture : IAsyncLifetime
{
    private DockerClient? _dockerClient;
    private string? _milvusContainerId;

    public Task InitializeAsync() => Task.CompletedTask;

    public async Task ManualInitializeAsync()
    {
        if (this._milvusContainerId is null)
        {
            using var dockerClientConfiguration = new DockerClientConfiguration();
            this._dockerClient = dockerClientConfiguration.CreateClient();
            this._milvusContainerId = await VectorStoreInfra.SetupMilvusContainerAsync(this._dockerClient);
        }

        // Milvus must finish starting before the sample creates collections.
        using var milvusClient = new MilvusClient("localhost");
        using var timeout = new CancellationTokenSource(TimeSpan.FromMinutes(2));
        while (true)
        {
            try
            {
                await milvusClient.ListCollectionsAsync(cancellationToken: timeout.Token);
                return;
            }
            catch (RpcException) when (!timeout.IsCancellationRequested)
            {
                await Task.Delay(1000, timeout.Token);
            }
        }
    }

    public async Task DisposeAsync()
    {
        if (this._dockerClient is not null)
        {
            try
            {
                if (this._milvusContainerId is not null)
                {
                    await VectorStoreInfra.DeleteContainerAsync(this._dockerClient, this._milvusContainerId);
                }
            }
            finally
            {
                this._dockerClient.Dispose();
            }
        }
    }
}
