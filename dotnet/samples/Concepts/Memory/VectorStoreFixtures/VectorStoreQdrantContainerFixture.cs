// Copyright (c) Microsoft. All rights reserved.

using Docker.DotNet;

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
        // Connect to docker and start the docker container.
        using var dockerClientConfiguration = new DockerClientConfiguration();
        this._dockerClient = dockerClientConfiguration.CreateClient();
        this._qdrantContainerId = await VectorStoreInfra.SetupQdrantContainerAsync(this._dockerClient);
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
