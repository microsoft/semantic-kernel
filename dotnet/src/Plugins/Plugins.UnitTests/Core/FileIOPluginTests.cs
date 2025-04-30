// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.Core;
using Xunit;

namespace SemanticKernel.Plugins.UnitTests.Core;

public class FileIOPluginTests
{
    [Fact]
    public void ItCanBeInstantiated()
    {
        // Act - Assert no exception occurs
        _ = new FileIOPlugin();
    }

    [Fact]
    public void ItCanBeImported()
    {
        // Act - Assert no exception occurs e.g. due to reflection
        Assert.NotNull(KernelPluginFactory.CreateFromType<FileIOPlugin>("fileIO"));
    }

    [Fact]
    public async Task ItCanReadAsync()
    {
        // Arrange
        var plugin = new FileIOPlugin();
        var path = Path.GetTempFileName();
        await File.WriteAllTextAsync(path, "hello world");

        // Act
        var result = await plugin.ReadAsync(path);

        // Assert
        Assert.Equal("hello world", result);
    }

    [Fact]
    public async Task ItCannotReadAsync()
    {
        // Arrange
        var plugin = new FileIOPlugin();
        var path = Path.GetTempFileName();
        File.Delete(path);

        // Act
        Task Fn()
        {
            return plugin.ReadAsync(path);
        }

        // Assert
        _ = await Assert.ThrowsAsync<FileNotFoundException>(Fn);
    }

    [Fact]
    public async Task ItCanWriteAsync()
    {
        // Arrange
        var plugin = new FileIOPlugin();
        var path = Path.GetTempFileName();

        // Act
        await plugin.WriteAsync(path, "hello world");

        // Assert
        Assert.Equal("hello world", await File.ReadAllTextAsync(path));
    }

    [Fact]
    public async Task ItCannotWriteAsync()
    {
        // Arrange
        var plugin = new FileIOPlugin();
        var path = Path.GetTempFileName();
        File.SetAttributes(path, FileAttributes.ReadOnly);

        // Act
        Task Fn()
        {
            return plugin.WriteAsync(path, "hello world");
        }

        // Assert
        _ = await Assert.ThrowsAsync<UnauthorizedAccessException>(Fn);
    }

    [Fact]
    public async Task ItCannotWriteToDisallowedFoldersAsync()
    {
        // Arrange
        var plugin = new FileIOPlugin()
        {
            AllowedFolders = [Path.GetTempPath()]
        };

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(async () => await plugin.WriteAsync(Path.Combine("C:", Path.GetRandomFileName()), "hello world"));
        await Assert.ThrowsAsync<ArgumentException>(async () => await plugin.WriteAsync(Path.Combine(Path.GetRandomFileName()), "hello world"));
        await Assert.ThrowsAsync<ArgumentException>(async () => await plugin.WriteAsync(Path.Combine("\\\\UNC\\server\\folder\\myfile.txt", Path.GetRandomFileName()), "hello world"));
        await Assert.ThrowsAsync<ArgumentException>(async () => await plugin.WriteAsync(Path.Combine("", Path.GetRandomFileName()), "hello world"));
    }

    [Fact]
    public async Task ItCannotReadFromDisallowedFoldersAsync()
    {
        // Arrange
        var plugin = new FileIOPlugin()
        {
            AllowedFolders = [Path.GetTempPath()]
        };

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(async () => await plugin.ReadAsync(Path.Combine("C:", Path.GetRandomFileName())));
        await Assert.ThrowsAsync<ArgumentException>(async () => await plugin.ReadAsync(Path.Combine(Path.GetRandomFileName())));
        await Assert.ThrowsAsync<ArgumentException>(async () => await plugin.ReadAsync(Path.Combine("\\\\UNC\\server\\folder\\myfile.txt", Path.GetRandomFileName())));
        await Assert.ThrowsAsync<ArgumentException>(async () => await plugin.ReadAsync(Path.Combine("", Path.GetRandomFileName())));
    }
}
