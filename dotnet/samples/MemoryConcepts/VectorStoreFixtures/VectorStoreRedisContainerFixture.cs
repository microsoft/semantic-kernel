// Copyright (c) Microsoft. All rights reserved.

using Docker.DotNet;

namespace Memory.VectorStoreFixtures;

/// <summary>
/// Fixture to use for creating a Redis container before tests and delete it after tests.
/// </summary>
public class VectorStoreRedisContainerFixture : IAsyncLifetime
{
    private DockerClient? _dockerClient;
    private string? _redisContainerId;

    public async Task InitializeAsync()
    {
    }

    public async Task ManualInitializeAsync()
    {
        if (this._redisContainerId == null)
        {
            // Connect to docker and start the docker container.
            using var dockerClientConfiguration = new DockerClientConfiguration();
            this._dockerClient = dockerClientConfiguration.CreateClient();
            this._redisContainerId = await VectorStoreInfra.SetupRedisContainerAsync(this._dockerClient);
        }
    }

    public async Task DisposeAsync()
    {
        if (this._dockerClient != null && this._redisContainerId != null)
        {
            // Delete docker container.
            await VectorStoreInfra.DeleteContainerAsync(this._dockerClient, this._redisContainerId);
        }
    }
}
