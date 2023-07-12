// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Services.Diagnostics;

namespace Microsoft.SemanticKernel.Services.Storage.ContentStorage;

public class FileSystem : IContentStorage
{
    // Parent directory of the directory containing messages
    private readonly string _directory;

    // Application logger
    private readonly ILogger<FileSystem> _log;

    public FileSystem(string directory) : this(directory, NullLogger<FileSystem>.Instance)
    {
    }

    public FileSystem(string directory, ILogger<FileSystem> logger)
    {
        this._log = logger;
        this.CreateDirectory(directory);
        this._directory = directory;
    }

    /// <inherit />
    public Task CreateDirectoryAsync(string directoryName, CancellationToken cancellationToken = default)
    {
        var path = Path.Join(this._directory, directoryName);

        if (!Directory.Exists(path))
        {
            Directory.CreateDirectory(path);
        }

        return Task.CompletedTask;
    }

    /// <inherit />
    public async Task WriteTextFileAsync(string directoryName, string fileName, string fileContent, CancellationToken cancellationToken = default)
    {
        await this.CreateDirectoryAsync(directoryName, cancellationToken).ConfigureAwait(false);
        var path = Path.Join(this._directory, directoryName, fileName);
        await File.WriteAllTextAsync(path, fileContent, cancellationToken).ConfigureAwait(false);
    }

    /// <inherit />
    public async Task<long> WriteStreamAsync(string directoryName, string fileName, Stream contentStream, CancellationToken cancellationToken = default)
    {
        await this.CreateDirectoryAsync(directoryName, cancellationToken).ConfigureAwait(false);
        var path = Path.Join(this._directory, directoryName, fileName);
        FileStream outputStream = File.Create(path);
        contentStream.Seek(0, SeekOrigin.Begin);
        await contentStream.CopyToAsync(outputStream, cancellationToken).ConfigureAwait(false);
        var size = outputStream.Length;
        outputStream.Close();
        return size;
    }

    /// <inherit />
    public Task<BinaryData> ReadFileAsync(string directoryName, string fileName, CancellationToken cancellationToken = default)
    {
        var path = Path.Join(this._directory, directoryName, fileName);
        if (!File.Exists(path))
        {
            throw new ContentStorageException("File not found");
        }

        byte[] data = File.ReadAllBytes(path);
        return Task.FromResult(new BinaryData(data));
    }

    private void CreateDirectory(string path)
    {
        if (string.IsNullOrEmpty(path))
        {
            return;
        }

        if (!Directory.Exists(path))
        {
            Directory.CreateDirectory(path);
        }
    }
}
