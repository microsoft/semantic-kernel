// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Docker.DotNet;
using Docker.DotNet.Models;
using Microsoft.Extensions.VectorData;
using MongoDB.Driver;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.MongoDB;

public class MongoDBVectorStoreFixture : IAsyncLifetime
{
    private readonly List<string> _testCollections = ["sk-test-hotels", "sk-test-contacts", "sk-test-addresses"];

    /// <summary>Main test collection for tests.</summary>
    public string TestCollection => this._testCollections[0];

    /// <summary><see cref="IMongoDatabase"/> that can be used to manage the collections in MongoDB.</summary>
    public IMongoDatabase MongoDatabase { get; }

    /// <summary>Gets the manually created vector store record definition for MongoDB test model.</summary>
    public VectorStoreRecordDefinition HotelVectorStoreRecordDefinition { get; private set; }

    /// <summary>The id of the MongoDB container that we are testing with.</summary>
    private string? _containerId = null;

    /// <summary>The Docker client we are using to create a MongoDB container with.</summary>
    private readonly DockerClient _client;

    /// <summary>
    /// Initializes a new instance of the <see cref="MongoDBVectorStoreFixture"/> class.
    /// </summary>
    public MongoDBVectorStoreFixture()
    {
        using var dockerClientConfiguration = new DockerClientConfiguration();
        this._client = dockerClientConfiguration.CreateClient();

        var mongoClient = new MongoClient("mongodb://localhost:27017/?directConnection=true");

        this.MongoDatabase = mongoClient.GetDatabase("test");

        this.HotelVectorStoreRecordDefinition = new()
        {
            Properties =
            [
                new VectorStoreRecordKeyProperty("HotelId", typeof(string)),
                new VectorStoreRecordDataProperty("HotelName", typeof(string)),
                new VectorStoreRecordDataProperty("HotelCode", typeof(int)),
                new VectorStoreRecordDataProperty("ParkingIncluded", typeof(bool)) { StoragePropertyName = "parking_is_included" },
                new VectorStoreRecordDataProperty("HotelRating", typeof(float)),
                new VectorStoreRecordDataProperty("Tags", typeof(List<string>)),
                new VectorStoreRecordDataProperty("Timestamp", typeof(DateTime)),
                new VectorStoreRecordDataProperty("Description", typeof(string)),
                new VectorStoreRecordVectorProperty("DescriptionEmbedding", typeof(ReadOnlyMemory<float>?)) { Dimensions = 4, IndexKind = IndexKind.IvfFlat, DistanceFunction = DistanceFunction.CosineSimilarity }
            ]
        };
    }

    public async Task InitializeAsync()
    {
        this._containerId = await SetupMongoDBContainerAsync(this._client);

        foreach (var collection in this._testCollections)
        {
            await this.MongoDatabase.CreateCollectionAsync(collection);
        }
    }

    public async Task DisposeAsync()
    {
        var cursor = await this.MongoDatabase.ListCollectionNamesAsync();

        while (await cursor.MoveNextAsync().ConfigureAwait(false))
        {
            foreach (var collection in cursor.Current)
            {
                await this.MongoDatabase.DropCollectionAsync(collection);
            }
        }

        if (this._containerId != null)
        {
            await this._client.Containers.StopContainerAsync(this._containerId, new ContainerStopParameters());
            await this._client.Containers.RemoveContainerAsync(this._containerId, new ContainerRemoveParameters());
        }
    }

    #region private

    private static async Task<string> SetupMongoDBContainerAsync(DockerClient client)
    {
        const string Image = "mongodb/mongodb-atlas-local";
        const string Tag = "latest";

        await client.Images.CreateImageAsync(
            new ImagesCreateParameters
            {
                FromImage = Image,
                Tag = Tag,
            },
            null,
            new Progress<JSONMessage>());

        var container = await client.Containers.CreateContainerAsync(new CreateContainerParameters()
        {
            Image = $"{Image}:{Tag}",
            HostConfig = new HostConfig()
            {
                PortBindings = new Dictionary<string, IList<PortBinding>>
                {
                    { "27017", new List<PortBinding> { new() { HostPort = "27017" } } },
                },
                PublishAllPorts = true
            },
            ExposedPorts = new Dictionary<string, EmptyStruct>
            {
                { "27017", default },
            },
        });

        await client.Containers.StartContainerAsync(
            container.ID,
            new ContainerStartParameters());

        return container.ID;
    }

    #endregion
}
