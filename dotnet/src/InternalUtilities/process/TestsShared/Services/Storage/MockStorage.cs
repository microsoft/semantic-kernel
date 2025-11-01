﻿// Copyright (c) Microsoft. All rights reserved.
#pragma warning disable IDE0005 // Using directive is unnecessary
using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading.Tasks;
#pragma warning restore IDE0005 // Using directive is unnecessary

namespace Microsoft.SemanticKernel.Process.TestsShared.Services.Storage;

#pragma warning disable CA1812 // Avoid uninstantiated internal classes
internal sealed class MockStorage : IProcessStorageConnector
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
{
    internal readonly Dictionary<string, MockStorageEntry> _dbMock = [];

    public bool ConnectionOpened { get; private set; } = false;
    public bool ConnectionClosed { get; private set; } = false;

    public ValueTask OpenConnectionAsync()
    {
        Console.WriteLine("Mock opening connection");
        this.ConnectionOpened = true;
        return ValueTask.CompletedTask;
    }
    public ValueTask CloseConnectionAsync()
    {
        Console.WriteLine("Mock closing connection");
        this.ConnectionClosed = true;
        return ValueTask.CompletedTask;
    }

    public Task<bool> DeleteEntryAsync(string id)
    {
        throw new System.NotImplementedException();
    }

    public Task<TEntry?> GetEntryAsync<TEntry>(string id) where TEntry : class
    {
        if (this._dbMock.TryGetValue(id, out var entry) && entry != null)
        {
            var deserializedEntry = JsonSerializer.Deserialize<TEntry>(entry.Content);
            return Task.FromResult(deserializedEntry);
        }

        return Task.FromResult<TEntry?>(null);
    }

    public Task<bool> SaveEntryAsync<TEntry>(string id, string type, TEntry entry) where TEntry : class
    {
        this._dbMock[id] = new() { Id = id, Type = type, Content = JsonSerializer.Serialize(entry) };

        return Task.FromResult(true);
    }
}

/// <summary>
/// Mock storage entry used for testing purposes.
/// </summary>
public record MockStorageEntry
{
    /// <summary>
    /// Unique identifier for the entry.
    /// </summary>
    public string Id { get; set; } = string.Empty;

    /// <summary>
    /// Type of the entry.
    /// </summary>
    public string Type { get; set; } = string.Empty;

    /// <summary>
    /// Serialized content of the entry.
    /// </summary>
    public string Content { get; set; } = string.Empty;
}
