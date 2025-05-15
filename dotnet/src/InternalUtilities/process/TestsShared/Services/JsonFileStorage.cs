// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;

namespace SemanticKernel.Process.TestsShared.Services;

internal sealed class JsonFileStorage : IProcessStorageConnector
{
    private readonly string _storageDirectory;

    private readonly JsonSerializerOptions _jsonSerializerOptions = new()
    {
        WriteIndented = true,
    };

    public JsonFileStorage(string storageDirectory)
    {
        this._storageDirectory = storageDirectory;
        Directory.CreateDirectory(this._storageDirectory);
    }

    public async ValueTask OpenConnectionAsync()
    {
        // For file-based storage, there's no real "connection" to open.  
        // This method might be used to validate if the storage directory is accessible.  
        await Task.CompletedTask;
    }

    public async ValueTask CloseConnectionAsync()
    {
        // For file-based storage, there's no real "connection" to close.  
        await Task.CompletedTask;
    }

    private string GetFilePath(string id)
    {
        return Path.Combine(this._storageDirectory, $"{id}.json");
    }

    public async Task<TEntry?> GetEntryAsync<TEntry>(string id) where TEntry : class
    {
        string filePath = this.GetFilePath(id);
        if (!File.Exists(filePath))
        {
            return null;
        }

        string jsonData = await File.ReadAllTextAsync(filePath);
        return JsonSerializer.Deserialize<TEntry>(jsonData);
    }

    public async Task<bool> SaveEntryAsync<TEntry>(string id, string type, TEntry entry) where TEntry : class
    {
        string filePath = this.GetFilePath(id);
        string jsonData = JsonSerializer.Serialize(entry, this._jsonSerializerOptions);

        await File.WriteAllTextAsync(filePath, jsonData);
        return true;
    }

    public Task<bool> DeleteEntryAsync(string id)
    {
        string filePath = this.GetFilePath(id);
        if (File.Exists(filePath))
        {
            File.Delete(filePath);
            return Task.FromResult(true);
        }

        return Task.FromResult(false);
    }
}
