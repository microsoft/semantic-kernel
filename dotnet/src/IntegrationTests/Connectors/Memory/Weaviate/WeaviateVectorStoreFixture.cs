// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net;
using System.Net.Http;
using System.Threading.Tasks;
using Docker.DotNet;
using Docker.DotNet.Models;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Weaviate;

public class WeaviateVectorStoreFixture : IAsyncLifetime
{
    /// <summary>The Docker client we are using to create a Weaviate container with.</summary>
    private readonly DockerClient _client;

    /// <summary>The id of the Weaviate container that we are testing with.</summary>
    private string? _containerId = null;

    public HttpClient? HttpClient { get; private set; }

    public WeaviateVectorStoreFixture()
    {
        using var dockerClientConfiguration = new DockerClientConfiguration();
        this._client = dockerClientConfiguration.CreateClient();
    }

    public async Task InitializeAsync()
    {
        this._containerId = await SetupWeaviateContainerAsync(this._client);

        this.HttpClient = new HttpClient { BaseAddress = new Uri("http://localhost:8080/v1/") };

        await WaitForInitializationAsync(this.HttpClient);
    }

    public async Task DisposeAsync()
    {
        if (this._containerId != null)
        {
            await this._client.Containers.StopContainerAsync(this._containerId, new ContainerStopParameters());
            await this._client.Containers.RemoveContainerAsync(this._containerId, new ContainerRemoveParameters());
        }
    }

    #region private

    private async static Task WaitForInitializationAsync(HttpClient httpClient)
    {
        const int MaxAttemptCount = 10;
        const int DelayInterval = 1000;

        int attemptCount = 0;
        bool clusterReady = false;

        do
        {
            await Task.Delay(DelayInterval);
            attemptCount++;
            clusterReady = await CheckIfClusterReadyAsync(httpClient);
        } while (!clusterReady && attemptCount <= MaxAttemptCount);

        if (!clusterReady)
        {
            throw new InvalidOperationException("Weaviate cluster is not ready for usage.");
        }
    }

    private static async Task<bool> CheckIfClusterReadyAsync(HttpClient httpClient)
    {
        try
        {
            var response = await httpClient.GetAsync(new Uri("schema", UriKind.Relative));

            return response.StatusCode == HttpStatusCode.OK;
        }
        catch (HttpRequestException)
        {
            return false;
        }
    }

    private static async Task<string> SetupWeaviateContainerAsync(DockerClient client)
    {
        const string Image = "cr.weaviate.io/semitechnologies/weaviate";
        const string Tag = "1.26.4";

        await client.Images.CreateImageAsync(
            new ImagesCreateParameters
            {
                FromImage = Image,
                Tag = "latest",
                Tag = Tag,
            },
            null,
            new Progress<JSONMessage>());

        var container = await client.Containers.CreateContainerAsync(new CreateContainerParameters()
        {
            Image = Image,
            Image = $"{Image}:{Tag}",
            HostConfig = new HostConfig()
            {
                PortBindings = new Dictionary<string, IList<PortBinding>>
                {
                    { "8080", new List<PortBinding> { new() { HostPort = "8080" } } },
                    { "50051", new List<PortBinding> { new() { HostPort = "50051" } } }
                },
                PublishAllPorts = true
            },
            ExposedPorts = new Dictionary<string, EmptyStruct>
            {
                { "8080", default },
                { "50051", default }
            },
        });

        await client.Containers.StartContainerAsync(
            container.ID,
            new ContainerStartParameters());

        return container.ID;
    }

    #endregion
}
