// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Docker.DotNet;
using Docker.DotNet.Models;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.PgVector;
using Npgsql;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.PgVector;

public class PostgresVectorStoreFixture : IAsyncLifetime
{
    /// <summary>The docker client we are using to create a postgres container with.</summary>
    private readonly DockerClient _client;

    /// <summary>The id of the postgres container that we are testing with.</summary>
    private string? _containerId = null;

#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.

    /// <summary>
    /// Initializes a new instance of the <see cref="PostgresVectorStoreFixture"/> class.
    /// </summary>
    public PostgresVectorStoreFixture()
    {
        using var dockerClientConfiguration = new DockerClientConfiguration();
        this._client = dockerClientConfiguration.CreateClient();
    }

    /// <summary>
    /// Holds the Npgsql data source to use for tests.
    /// </summary>
    public NpgsqlDataSource? DataSource { get; private set; }

    private string _connectionString = null!;
    private string _databaseName = null!;

    /// <summary>
    /// Gets a vector store to use for tests.
    /// </summary>
    public VectorStore VectorStore => new PostgresVectorStore(this.DataSource!, ownsDataSource: false);

    /// <summary>
    /// Get a database connection
    /// </summary>
    public NpgsqlConnection GetConnection()
    {
        return this.DataSource!.OpenConnection();
    }

    public VectorStoreCollection<TKey, TRecord> GetCollection<TKey, TRecord>(
        string collectionName,
        VectorStoreCollectionDefinition? definition = default)
        where TKey : notnull
        where TRecord : class
    {
        var vectorStore = this.VectorStore;
        return vectorStore.GetCollection<TKey, TRecord>(collectionName, definition);
    }

    public VectorStoreCollection<object, Dictionary<string, object?>> GetDynamicCollection(
        string collectionName,
        VectorStoreCollectionDefinition definition)
    {
        var vectorStore = this.VectorStore;
        return vectorStore.GetDynamicCollection(collectionName, definition);
    }

    /// <summary>
    /// Create / Recreate postgres docker container and run it.
    /// </summary>
    /// <returns>An async task.</returns>
    public async Task InitializeAsync()
    {
        this._containerId = await SetupPostgresContainerAsync(this._client);
        this._connectionString = "Host=localhost;Port=5432;Username=postgres;Password=example;Database=postgres;";
        this._databaseName = $"sk_it_{Guid.NewGuid():N}";

        // Connect to postgres.
        NpgsqlConnectionStringBuilder connectionStringBuilder = new(this._connectionString)
        {
            Database = this._databaseName
        };

        NpgsqlDataSourceBuilder dataSourceBuilder = new(connectionStringBuilder.ToString());
        dataSourceBuilder.UseVector();

        this.DataSource = dataSourceBuilder.Build();

        // Wait for the postgres container to be ready and create the test database using the initial data source.
        var initialDataSource = NpgsqlDataSource.Create(this._connectionString);
        using (initialDataSource)
        {
            var retryCount = 0;
            var exceptionCount = 0;
            while (retryCount++ < 5)
            {
                try
                {
                    NpgsqlConnection connection = await initialDataSource.OpenConnectionAsync().ConfigureAwait(false);

                    await using (connection)
                    {
                        using NpgsqlCommand cmd = connection.CreateCommand();
                        cmd.CommandText = "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';";
                        await cmd.ExecuteScalarAsync().ConfigureAwait(false);
                    }
                }
                catch (NpgsqlException)
                {
                    exceptionCount++;
                    await Task.Delay(1000);
                }
            }

            if (exceptionCount >= 5)
            {
                // Throw an exception for test setup
                throw new InvalidOperationException("Postgres container did not start in time.");
            }

            await this.CreateDatabaseAsync(initialDataSource);
        }

        // Create the table.
        await this.CreateTableAsync();
    }

    private async Task CreateTableAsync()
    {
        NpgsqlConnection connection = await this.DataSource!.OpenConnectionAsync().ConfigureAwait(false);

        await using (connection)
        {
            using NpgsqlCommand cmd = connection.CreateCommand();
            cmd.CommandText = @"
                CREATE TABLE hotel_info (
                    HotelId INTEGER NOT NULL,
                    HotelName TEXT,
                    HotelCode INTEGER NOT NULL,
                    HotelRating REAL,
                    parking_is_included BOOLEAN,
                    Tags TEXT[] NOT NULL,
                    Description TEXT NOT NULL,
                    DescriptionEmbedding VECTOR(4) NOT NULL,
                    PRIMARY KEY (HotelId));";
            await cmd.ExecuteNonQueryAsync().ConfigureAwait(false);
        }
    }

    /// <summary>
    /// Delete the docker container after the test run.
    /// </summary>
    /// <returns>An async task.</returns>
    public async Task DisposeAsync()
    {
        if (this.DataSource != null)
        {
            this.DataSource.Dispose();
        }

        await this.DropDatabaseAsync();

        if (this._containerId != null)
        {
            await this._client.Containers.StopContainerAsync(this._containerId, new ContainerStopParameters());
            await this._client.Containers.RemoveContainerAsync(this._containerId, new ContainerRemoveParameters());
        }
    }

    /// <summary>
    /// Setup the postgres container by pulling the image and running it.
    /// </summary>
    /// <param name="client">The docker client to create the container with.</param>
    /// <returns>The id of the container.</returns>
    private static async Task<string> SetupPostgresContainerAsync(DockerClient client)
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
            Env =
            [
                "POSTGRES_USER=postgres",
                "POSTGRES_PASSWORD=example",
            ],
        });

        await client.Containers.StartContainerAsync(
            container.ID,
            new ContainerStartParameters());

        return container.ID;
    }

    [System.Diagnostics.CodeAnalysis.SuppressMessage("Security", "CA2100:Review SQL queries for security vulnerabilities", Justification = "The database name is generated randomly, it does not support parameterized passing.")]
    private async Task CreateDatabaseAsync(NpgsqlDataSource initialDataSource)
    {
        await using (NpgsqlConnection conn = await initialDataSource.OpenConnectionAsync())
        {
            await using NpgsqlCommand command = new($"CREATE DATABASE \"{this._databaseName}\"", conn);
            await command.ExecuteNonQueryAsync();
        }

        await using (NpgsqlConnection conn = await this.DataSource!.OpenConnectionAsync())
        {
            await using (NpgsqlCommand command = new("CREATE EXTENSION vector", conn))
            {
                await command.ExecuteNonQueryAsync();
            }
            await conn.ReloadTypesAsync();
        }
    }

    [System.Diagnostics.CodeAnalysis.SuppressMessage("Security", "CA2100:Review SQL queries for security vulnerabilities", Justification = "The database name is generated randomly, it does not support parameterized passing.")]
    private async Task DropDatabaseAsync()
    {
        using NpgsqlDataSource dataSource = NpgsqlDataSource.Create(this._connectionString);
        await using NpgsqlConnection conn = await dataSource.OpenConnectionAsync();
        await using NpgsqlCommand command = new($"DROP DATABASE IF EXISTS \"{this._databaseName}\"", conn);
        await command.ExecuteNonQueryAsync();
    }
}
