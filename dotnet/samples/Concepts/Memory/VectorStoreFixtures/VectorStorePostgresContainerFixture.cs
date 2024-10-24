// Copyright (c) Microsoft. All rights reserved.

using Docker.DotNet;
using Npgsql;

namespace Memory.VectorStoreFixtures;

/// <summary>
/// Fixture to use for creating a Postgres container before tests and delete it after tests.
/// </summary>
public class VectorStorePostgresContainerFixture : IAsyncLifetime
{
    private DockerClient? _dockerClient;
    private string? _postgresContainerId;

    public async Task InitializeAsync()
    {
    }

    public async Task ManualInitializeAsync()
    {
        if (this._postgresContainerId == null)
        {
            // Connect to docker and start the docker container.
            using var dockerClientConfiguration = new DockerClientConfiguration();
            this._dockerClient = dockerClientConfiguration.CreateClient();
            this._postgresContainerId = await VectorStoreInfra.SetupPostgresContainerAsync(this._dockerClient);

            // Delay until the Postgres server is ready.
            var connectionString = "Host=localhost;Port=5432;Username=postgres;Password=example;Database=postgres;";
            var succeeded = false;
            var attemptCount = 0;
            while (!succeeded && attemptCount++ < 10)
            {
                try
                {
                    NpgsqlDataSourceBuilder dataSourceBuilder = new(connectionString);
                    dataSourceBuilder.UseVector();
                    using var dataSource = dataSourceBuilder.Build();
                    NpgsqlConnection connection = await dataSource.OpenConnectionAsync().ConfigureAwait(false);

                    await using (connection)
                    {
                        // Create extension vector if it doesn't exist
                        await using (NpgsqlCommand command = new("CREATE EXTENSION IF NOT EXISTS vector", connection))
                        {
                            await command.ExecuteNonQueryAsync();
                        }
                    }
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
        if (this._dockerClient != null && this._postgresContainerId != null)
        {
            // Delete docker container.
            await VectorStoreInfra.DeleteContainerAsync(this._dockerClient, this._postgresContainerId);
        }
    }
}
