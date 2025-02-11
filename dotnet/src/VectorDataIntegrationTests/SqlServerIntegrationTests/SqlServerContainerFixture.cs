// Copyright (c) Microsoft. All rights reserved.

using Testcontainers.MsSql;
using Xunit;

namespace SqlServerIntegrationTests;

public sealed class SqlServerContainerFixture : IAsyncLifetime
{
    private MsSqlContainer? Container { get; set; }

    public string GetConnectionString() => this.Container?.GetConnectionString() ??
        throw new InvalidOperationException("The test container was not initialized.");

    public async Task DisposeAsync()
    {
        if (this.Container is not null)
        {
            await this.Container.DisposeAsync();
        }
    }

    public async Task InitializeAsync() => this.Container = await CreateContainerAsync();

    private static async Task<MsSqlContainer> CreateContainerAsync()
    {
        var container = new MsSqlBuilder()
            .WithImage("mcr.microsoft.com/mssql/server:2022-latest")
            .Build();

        await container.StartAsync();

        return container;
    }
}
