// Copyright (c) Microsoft. All rights reserved.

using ChromaDB.Client;
using Docker.DotNet;

namespace Memory.VectorStoreFixtures;

/// <summary>
/// Fixture to use for creating a Chroma container before tests and delete it after tests.
/// </summary>
public class VectorStoreChromaContainerFixture : IAsyncLifetime
{
    private DockerClient? _dockerClient;
    private string? _chromaContainerId;

    public async Task InitializeAsync()
    {
    }

    public async Task ManualInitializeAsync()
    {
        if (this._chromaContainerId == null)
        {
            // Connect to docker and start the docker container.
            using var dockerClientConfiguration = new DockerClientConfiguration();
            this._dockerClient = dockerClientConfiguration.CreateClient();
            this._chromaContainerId = await VectorStoreInfra.SetupChromaContainerAsync(this._dockerClient);

            // Delay until the Chroma server is ready.
            var chromaClient = new ChromaClient("http://localhost:8000");
            var succeeded = false;
            var attemptCount = 0;
            while (!succeeded && attemptCount++ < 10)
            {
                try
                {
                    await chromaClient.ListCollectionsAsync();
                    succeeded = true;
                }
                catch (Exception)
                {
                    await Task.Delay(1000);
                }
            }
        }
    }

    public async Task DisposeAsync()
    {
        if (this._dockerClient != null && this._chromaContainerId != null)
        {
            // Delete docker container.
            await VectorStoreInfra.DeleteContainerAsync(this._dockerClient, this._chromaContainerId);
        }
    }
}
