// Copyright (c) Microsoft. All rights reserved.

using Docker.DotNet;
using Qdrant.Client;

namespace Memory.VectorStoreFixtures;

/// <summary>
/// Fixture to use for creating a Qdrant container before tests and delete it after tests.
/// </summary>
public class VectorStoreQdrantContainerFixture : IAsyncLifetime
{
    private DockerClient? _dockerClient;
    private string? _qdrantContainerId;

    public async Task InitializeAsync()
    {
    }

    public async Task ManualInitializeAsync()
    {
        if (this._qdrantContainerId == null)
        {
            // Connect to docker and start the docker container.
            using var dockerClientConfiguration = new DockerClientConfiguration();
            this._dockerClient = dockerClientConfiguration.CreateClient();
            this._qdrantContainerId = await VectorStoreInfra.SetupQdrantContainerAsync(this._dockerClient);

            // Delay until the Qdrant server is ready.
            var qdrantClient = new QdrantClient("localhost");
            var succeeded = false;
            var attemptCount = 0;
            while (!succeeded && attemptCount++ < 10)
            {
                try
                {
                    await qdrantClient.ListCollectionsAsync();
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
        if (this._dockerClient != null && this._qdrantContainerId != null)
        {
            // Delete docker container.
            await VectorStoreInfra.DeleteContainerAsync(this._dockerClient, this._qdrantContainerId);
        }
    }
}
