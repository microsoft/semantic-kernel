// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using Docker.DotNet;
using Docker.DotNet.Models;
using Microsoft.SemanticKernel.Memory;
using NRedisStack.RedisStackCommands;
using NRedisStack.Search;
using StackExchange.Redis;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Redis;

#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.
/// <summary>
/// Does setup and teardown of redis docker container and associated test data.
/// </summary>
public class RedisVectorStoreFixture : IAsyncLifetime
{
    /// <summary>The docker client we are using to create a redis container with.</summary>
    private readonly DockerClient _client;

    /// <summary>The id of the redis container that we are testing with.</summary>
    private string? _containerId = null;

    /// <summary>
    /// Initializes a new instance of the <see cref="RedisVectorStoreFixture"/> class.
    /// </summary>
    public RedisVectorStoreFixture()
    {
        using var dockerClientConfiguration = new DockerClientConfiguration();
        this._client = dockerClientConfiguration.CreateClient();
        this.VectorStoreRecordDefinition = new VectorStoreRecordDefinition
        {
            Properties = new List<VectorStoreRecordProperty>
            {
                new VectorStoreRecordKeyProperty("HotelId"),
                new VectorStoreRecordDataProperty("HotelName"),
                new VectorStoreRecordDataProperty("HotelCode"),
                new VectorStoreRecordDataProperty("Description"),
                new VectorStoreRecordVectorProperty("DescriptionEmbedding"),
                new VectorStoreRecordDataProperty("Tags"),
                new VectorStoreRecordDataProperty("ParkingIncluded"),
                new VectorStoreRecordDataProperty("LastRenovationDate"),
                new VectorStoreRecordDataProperty("Rating"),
                new VectorStoreRecordDataProperty("Address")
            }
        };
    }

    /// <summary>Gets the redis database connection to use for tests.</summary>
    public IDatabase Database { get; private set; }

    /// <summary>Gets the manually created vector store record definition for our test model.</summary>
    public VectorStoreRecordDefinition VectorStoreRecordDefinition { get; private set; }

    /// <summary>
    /// Create / Recreate redis docker container, create an index and add test data.
    /// </summary>
    /// <returns>An async task.</returns>
    public async Task InitializeAsync()
    {
        this._containerId = await SetupRedisContainerAsync(this._client);

        // Connect to redis.
        ConnectionMultiplexer redis = ConnectionMultiplexer.Connect("localhost:6379");
        this.Database = redis.GetDatabase();

        // Create a schema for the vector store.
        var schema = new Schema();
        schema.AddTextField("HotelName");
        schema.AddNumericField("hotelCode");
        schema.AddTextField("Description");
        schema.AddVectorField("DescriptionEmbedding", Schema.VectorField.VectorAlgo.HNSW, new Dictionary<string, object>()
        {
            ["TYPE"] = "FLOAT32",
            ["DIM"] = "4",
            ["DISTANCE_METRIC"] = "L2"
        });
        var createParams = new FTCreateParams();
        createParams.AddPrefix("hotels");
        await this.Database.FT().CreateAsync("hotels", createParams, schema);

        // Create some test data.
        var address = new HotelAddress { City = "Seattle", Country = "USA" };
        var embedding = new[] { 30f, 31f, 32f, 33f };

        await this.Database.JSON().SetAsync("hotels:BaseSet-1", "$", new
        {
            HotelName = "My Hotel 1",
            HotelCode = 1,
            Description = "This is a great hotel.",
            DescriptionEmbedding = embedding,
            Tags = new[] { "pool", "air conditioning", "concierge" },
            parking_is_included = true,
            LastRenovationDate = new DateTimeOffset(1970, 1, 18, 0, 0, 0, TimeSpan.Zero),
            Rating = 3.6,
            Address = address
        });
        await this.Database.JSON().SetAsync("hotels:BaseSet-2", "$", new { HotelName = "My Hotel 2", HotelCode = 2, Description = "This is a great hotel.", DescriptionEmbedding = embedding, parking_is_included = false });
        await this.Database.JSON().SetAsync("hotels:BaseSet-3", "$", new { HotelName = "My Hotel 3", HotelCode = 3, Description = "This is a great hotel.", DescriptionEmbedding = embedding, parking_is_included = false });
        await this.Database.JSON().SetAsync("hotels:BaseSet-4-Invalid", "$", new { HotelId = "AnotherId", HotelName = "My Invalid Hotel", HotelCode = 4, Description = "This is an invalid hotel.", DescriptionEmbedding = embedding, parking_is_included = false });
    }

    /// <summary>
    /// Delete the docker container after the test run.
    /// </summary>
    /// <returns>An async task.</returns>
    public async Task DisposeAsync()
    {
        if (this._containerId != null)
        {
            await this._client.Containers.StopContainerAsync(this._containerId, new ContainerStopParameters());
            await this._client.Containers.RemoveContainerAsync(this._containerId, new ContainerRemoveParameters());
        }
    }

    /// <summary>
    /// Setup the redis container by pulling the image and running it.
    /// </summary>
    /// <param name="client">The docker client to create the container with.</param>
    /// <returns>The id of the container.</returns>
    private static async Task<string> SetupRedisContainerAsync(DockerClient client)
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
                    {"6379", new List<PortBinding> {new() {HostPort = "6379"}}}
                },
                PublishAllPorts = true
            },
            ExposedPorts = new Dictionary<string, EmptyStruct>
            {
                { "6379", default }
            },
        });

        await client.Containers.StartContainerAsync(
            container.ID,
            new ContainerStartParameters());

        return container.ID;
    }

    /// <summary>
    /// A test model for the vector store.
    /// </summary>
    public class Hotel
    {
        [VectorStoreRecordKey]
        public string HotelId { get; init; }

        [VectorStoreRecordData]
        public string HotelName { get; init; }

        [VectorStoreRecordData]
        public int HotelCode { get; init; }

        [VectorStoreRecordData(HasEmbedding = true, EmbeddingPropertyName = "DescriptionEmbedding")]
        public string Description { get; init; }

        [VectorStoreRecordVector]
        public ReadOnlyMemory<float>? DescriptionEmbedding { get; init; }

#pragma warning disable CA1819 // Properties should not return arrays
        [VectorStoreRecordData]
        public string[] Tags { get; init; }
#pragma warning restore CA1819 // Properties should not return arrays

        [JsonPropertyName("parking_is_included")]
        [VectorStoreRecordData]
        public bool ParkingIncluded { get; init; }

        [VectorStoreRecordData]
        public DateTimeOffset LastRenovationDate { get; init; }

        [VectorStoreRecordData]
        public double Rating { get; init; }

        [VectorStoreRecordData]
        public HotelAddress Address { get; init; }
    }

    /// <summary>
    /// A test model for the vector store to simulate a complex type.
    /// </summary>
    public class HotelAddress
    {
        public string City { get; init; }
        public string Country { get; init; }
    }
}
#pragma warning restore CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.
