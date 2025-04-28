// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Threading.Tasks;
using Docker.DotNet;
using Docker.DotNet.Models;
using Microsoft.Extensions.VectorData;
using NRedisStack.RedisStackCommands;
using NRedisStack.Search;
using NRedisStack.Search.Literals.Enums;
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
                new VectorStoreRecordKeyProperty("HotelId", typeof(string)),
                new VectorStoreRecordDataProperty("HotelName", typeof(string)) { IsIndexed = true },
                new VectorStoreRecordDataProperty("HotelCode", typeof(int)) { IsIndexed = true },
                new VectorStoreRecordDataProperty("Description", typeof(string)) { IsFullTextIndexed = true },
                new VectorStoreRecordVectorProperty("DescriptionEmbedding", typeof(ReadOnlyMemory<float>?), 4),
                new VectorStoreRecordDataProperty("Tags", typeof(string[])) { IsIndexed = true },
                new VectorStoreRecordDataProperty("FTSTags", typeof(string[])) { IsFullTextIndexed = true },
                new VectorStoreRecordDataProperty("ParkingIncluded", typeof(bool)) { StoragePropertyName = "parking_is_included" },
                new VectorStoreRecordDataProperty("LastRenovationDate", typeof(DateTimeOffset)),
                new VectorStoreRecordDataProperty("Rating", typeof(double)),
                new VectorStoreRecordDataProperty("Address", typeof(RedisHotelAddress))
            }
        };
        this.BasicVectorStoreRecordDefinition = new VectorStoreRecordDefinition
        {
            Properties = new List<VectorStoreRecordProperty>
            {
                new VectorStoreRecordKeyProperty("HotelId", typeof(string)),
                new VectorStoreRecordDataProperty("HotelName", typeof(string)) { IsIndexed = true },
                new VectorStoreRecordDataProperty("HotelCode", typeof(int)) { IsIndexed = true },
                new VectorStoreRecordDataProperty("Description", typeof(string)) { IsFullTextIndexed = true },
                new VectorStoreRecordVectorProperty("DescriptionEmbedding", typeof(ReadOnlyMemory<float>?), 4),
                new VectorStoreRecordDataProperty("ParkingIncluded", typeof(bool)) { StoragePropertyName = "parking_is_included" },
                new VectorStoreRecordDataProperty("Rating", typeof(double)),
            }
        };
    }

    /// <summary>Gets the redis database connection to use for tests.</summary>
    public IDatabase Database { get; private set; }

    /// <summary>Gets the manually created vector store record definition for our test model.</summary>
    public VectorStoreRecordDefinition VectorStoreRecordDefinition { get; private set; }

    /// <summary>Gets the manually created vector store record definition for our basic test model.</summary>
    public VectorStoreRecordDefinition BasicVectorStoreRecordDefinition { get; private set; }

    /// <summary>
    /// Create / Recreate redis docker container, create an index and add test data.
    /// </summary>
    /// <returns>An async task.</returns>
    public async Task InitializeAsync()
    {
        this._containerId = await SetupRedisContainerAsync(this._client);

        // Connect to redis.
        ConnectionMultiplexer redis = ConnectionMultiplexer.Connect("localhost:6379,connectTimeout=60000,connectRetry=5");
        this.Database = redis.GetDatabase();

        // Create a JSON index.
        var jsonSchema = new Schema();
        jsonSchema.AddTagField(new FieldName("$.HotelName", "HotelName"));
        jsonSchema.AddNumericField(new FieldName("$.HotelCode", "HotelCode"));
        jsonSchema.AddTextField(new FieldName("$.Description", "Description"));
        jsonSchema.AddTagField(new FieldName("$.Tags", "Tags"));
        jsonSchema.AddTextField(new FieldName("$.FTSTags", "FTSTags"));
        jsonSchema.AddVectorField(new FieldName("$.DescriptionEmbedding", "DescriptionEmbedding"), Schema.VectorField.VectorAlgo.HNSW, new Dictionary<string, object>()
        {
            ["TYPE"] = "FLOAT32",
            ["DIM"] = "4",
            ["DISTANCE_METRIC"] = "L2"
        });
        var jsonCreateParams = new FTCreateParams().AddPrefix("jsonhotels:").On(IndexDataType.JSON);
        await this.Database.FT().CreateAsync("jsonhotels", jsonCreateParams, jsonSchema);

        // Create a hashset index.
        var hashSchema = new Schema();
        hashSchema.AddTagField(new FieldName("HotelName", "HotelName"));
        hashSchema.AddNumericField(new FieldName("HotelCode", "HotelCode"));
        hashSchema.AddTextField(new FieldName("Description", "Description"));
        hashSchema.AddVectorField(new FieldName("DescriptionEmbedding", "DescriptionEmbedding"), Schema.VectorField.VectorAlgo.HNSW, new Dictionary<string, object>()
        {
            ["TYPE"] = "FLOAT32",
            ["DIM"] = "4",
            ["DISTANCE_METRIC"] = "L2"
        });

        var hashsetCreateParams = new FTCreateParams().AddPrefix("hashhotels:").On(IndexDataType.HASH);
        await this.Database.FT().CreateAsync("hashhotels", hashsetCreateParams, hashSchema);

        // Create some test data.
        var address = new RedisHotelAddress { City = "Seattle", Country = "USA" };
        var embedding = new[] { 30f, 31f, 32f, 33f };

        // Add JSON test data.
        await this.Database.JSON().SetAsync("jsonhotels:BaseSet-1", "$", new
        {
            HotelName = "My Hotel 1",
            HotelCode = 1,
            Description = "This is a great hotel.",
            DescriptionEmbedding = embedding,
            Tags = new[] { "pool", "air conditioning", "concierge" },
            FTSTags = new[] { "pool", "air conditioning", "concierge" },
            parking_is_included = true,
            LastRenovationDate = new DateTimeOffset(1970, 1, 18, 0, 0, 0, TimeSpan.Zero),
            Rating = 3.6,
            Address = address
        });
        await this.Database.JSON().SetAsync("jsonhotels:BaseSet-2", "$", new { HotelName = "My Hotel 2", HotelCode = 2, Description = "This is a great hotel.", DescriptionEmbedding = embedding, parking_is_included = false });
        await this.Database.JSON().SetAsync("jsonhotels:BaseSet-3", "$", new { HotelName = "My Hotel 3", HotelCode = 3, Description = "This is a great hotel.", DescriptionEmbedding = embedding, parking_is_included = false });
        await this.Database.JSON().SetAsync("jsonhotels:BaseSet-4-Invalid", "$", new { HotelId = "AnotherId", HotelName = "My Invalid Hotel", HotelCode = 4, Description = "This is an invalid hotel.", DescriptionEmbedding = embedding, parking_is_included = false });

        // Add hashset test data.
        await this.Database.HashSetAsync("hashhotels:HBaseSet-1", new HashEntry[]
        {
            new("HotelName", "My Hotel 1"),
            new("HotelCode", 1),
            new("Description", "This is a great hotel."),
            new("DescriptionEmbedding", MemoryMarshal.AsBytes(new ReadOnlySpan<float>(embedding)).ToArray()),
            new("parking_is_included", true),
            new("Rating", 3.6)
        });
        await this.Database.HashSetAsync("hashhotels:HBaseSet-2", new HashEntry[]
        {
            new("HotelName", "My Hotel 2"),
            new("HotelCode", 2),
            new("Description", "This is a great hotel."),
            new("DescriptionEmbedding", MemoryMarshal.AsBytes(new ReadOnlySpan<float>(embedding)).ToArray()),
            new("parking_is_included", false),
        });
        await this.Database.HashSetAsync("hashhotels:HBaseSet-3", new HashEntry[]
        {
            new("HotelName", "My Hotel 3"),
            new("HotelCode", 3),
            new("Description", "This is a great hotel."),
            new("DescriptionEmbedding", MemoryMarshal.AsBytes(new ReadOnlySpan<float>(embedding)).ToArray()),
            new("parking_is_included", false),
        });
        await this.Database.HashSetAsync("hashhotels:HBaseSet-4-Invalid", new HashEntry[]
        {
            new("HotelId", "AnotherId"),
            new("HotelName", "My Invalid Hotel"),
            new("HotelCode", 4),
            new("Description", "This is an invalid hotel."),
            new("DescriptionEmbedding", MemoryMarshal.AsBytes(new ReadOnlySpan<float>(embedding)).ToArray()),
            new("parking_is_included", false),
        });
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

        await Task.Delay(1000);

        return container.ID;
    }
}
