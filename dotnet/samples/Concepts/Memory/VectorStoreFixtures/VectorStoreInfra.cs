// Copyright (c) Microsoft. All rights reserved.

using Docker.DotNet;
using Docker.DotNet.Models;

namespace Memory.VectorStoreFixtures;

/// <summary>
/// Helper class that creates and deletes containers for the vector store examples.
/// </summary>
internal static class VectorStoreInfra
{
    /// <summary>
    /// Setup the postgres pgvector container by pulling the image and running it.
    /// </summary>
    /// <param name="client">The docker client to create the container with.</param>
    /// <returns>The id of the container.</returns>
    public static async Task<string> SetupPostgresContainerAsync(DockerClient client)
    {
        await client.Images.CreateImageAsync(
            new ImagesCreateParameters
            {
                FromImage = "pgvector/pgvector",
                Tag = "pg16",
            },
            null,
            new Progress<JSONMessage>());

        var container = await client.Containers.CreateContainerAsync(new CreateContainerParameters()
        {
            Image = "pgvector/pgvector:pg16",
            HostConfig = new HostConfig()
            {
                PortBindings = new Dictionary<string, IList<PortBinding>>
                {
                    {"5432", new List<PortBinding> {new() {HostPort = "5432" } }},
                },
                PublishAllPorts = true
            },
            ExposedPorts = new Dictionary<string, EmptyStruct>
            {
               { "5432", default },
            },
            Env = new List<string>
            {
                "POSTGRES_USER=postgres",
                "POSTGRES_PASSWORD=example",
            },
        });

        await client.Containers.StartContainerAsync(
            container.ID,
            new ContainerStartParameters());

        return container.ID;
    }

    /// <summary>
    /// Setup the qdrant container by pulling the image and running it.
    /// </summary>
    /// <param name="client">The docker client to create the container with.</param>
    /// <returns>The id of the container.</returns>
    public static async Task<string> SetupQdrantContainerAsync(DockerClient client)
    {
        await client.Images.CreateImageAsync(
            new ImagesCreateParameters
            {
                FromImage = "qdrant/qdrant",
                Tag = "latest",
            },
            null,
            new Progress<JSONMessage>());

        var container = await client.Containers.CreateContainerAsync(new CreateContainerParameters()
        {
            Image = "qdrant/qdrant",
            HostConfig = new HostConfig()
            {
                PortBindings = new Dictionary<string, IList<PortBinding>>
                {
                    {"6333", new List<PortBinding> {new() {HostPort = "6333" } }},
                    {"6334", new List<PortBinding> {new() {HostPort = "6334" } }}
                },
                PublishAllPorts = true
            },
            ExposedPorts = new Dictionary<string, EmptyStruct>
            {
                { "6333", default },
                { "6334", default }
            },
        });

        await client.Containers.StartContainerAsync(
            container.ID,
            new ContainerStartParameters());

        return container.ID;
    }

    /// <summary>
    /// Setup the redis container by pulling the image and running it.
    /// </summary>
    /// <param name="client">The docker client to create the container with.</param>
    /// <returns>The id of the container.</returns>
    public static async Task<string> SetupRedisContainerAsync(DockerClient client)
    {
        await client.Images.CreateImageAsync(
            new ImagesCreateParameters
            {
                FromImage = "redis/redis-stack",
                Tag = "latest",
            },
            null,
            new Progress<JSONMessage>());

        var container = await client.Containers.CreateContainerAsync(new CreateContainerParameters()
        {
            Image = "redis/redis-stack",
            HostConfig = new HostConfig()
            {
                PortBindings = new Dictionary<string, IList<PortBinding>>
                {
                    {"6379", new List<PortBinding> {new() {HostPort = "6379"}}},
                    {"8001", new List<PortBinding> {new() {HostPort = "8001"}}}
                },
                PublishAllPorts = true
            },
            ExposedPorts = new Dictionary<string, EmptyStruct>
            {
                { "6379", default },
                { "8001", default }
            },
        });

        await client.Containers.StartContainerAsync(
            container.ID,
            new ContainerStartParameters());

        return container.ID;
    }

    /// <summary>
    /// Stop and delete the container with the specified id.
    /// </summary>
    /// <param name="client">The docker client to delete the container in.</param>
    /// <param name="containerId">The id of the container to delete.</param>
    /// <returns>An async task.</returns>
    public static async Task DeleteContainerAsync(DockerClient client, string containerId)
    {
        await client.Containers.StopContainerAsync(containerId, new ContainerStopParameters());
        await client.Containers.RemoveContainerAsync(containerId, new ContainerRemoveParameters());
    }
}
