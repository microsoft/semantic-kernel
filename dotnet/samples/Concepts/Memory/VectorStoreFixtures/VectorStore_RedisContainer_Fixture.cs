// Copyright (c) Microsoft. All rights reserved.

using Docker.DotNet;

namespace Memory.VectorStoreFixtures;

/// <summary>
/// Fixture to use for creating a Redis container before tests and delete it after tests.
/// </summary>
public class VectorStore_RedisContainer_Fixture : IAsyncLifetime
{
    private DockerClient? _dockerClient;
    private string? _redisContainerId;

    public async Task InitializeAsync()
    {
        // Connect to docker and start the docker container.
        using var dockerClientConfiguration = new DockerClientConfiguration();
        this._dockerClient = dockerClientConfiguration.CreateClient();
        this._redisContainerId = await VectorStore_Infra.SetupRedisContainerAsync(this._dockerClient);
    }

    public async Task DisposeAsync()
    {
        if (this._dockerClient != null && this._redisContainerId != null)
        {
            // Delete docker container.
            await VectorStore_Infra.DeleteContainerAsync(this._dockerClient, this._redisContainerId);
        }
    }
}
