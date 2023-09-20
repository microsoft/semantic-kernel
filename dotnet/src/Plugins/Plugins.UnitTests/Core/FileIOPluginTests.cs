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
        // Arrange
        var kernel = Kernel.Builder.Build();

        // Act - Assert no exception occurs e.g. due to reflection
        _ = kernel.ImportFunctions(new FileIOPlugin(), "fileIO");
    }

    [Fact]
    public async Task ItCanReadAsync()
    {
        // Arrange
        var skill = new FileIOPlugin();
        var path = Path.GetTempFileName();
        File.WriteAllText(path, "hello world");

        // Act
        var result = await skill.ReadAsync(path);

        // Assert
        Assert.Equal("hello world", result);
    }

    [Fact]
    public async Task ItCannotReadAsync()
    {
        // Arrange
        var skill = new FileIOPlugin();
        var path = Path.GetTempFileName();
        File.Delete(path);

        // Act
        Task Fn()
        {
            return skill.ReadAsync(path);
        }

        // Assert
        _ = await Assert.ThrowsAsync<FileNotFoundException>(Fn);
    }

    [Fact]
    public async Task ItCanWriteAsync()
    {
        // Arrange
        var skill = new FileIOPlugin();
        var path = Path.GetTempFileName();

        // Act
        await skill.WriteAsync(path, "hello world");

        // Assert
        Assert.Equal("hello world", await File.ReadAllTextAsync(path));
    }

    [Fact]
    public async Task ItCannotWriteAsync()
    {
        // Arrange
        var skill = new FileIOPlugin();
        var path = Path.GetTempFileName();
        File.SetAttributes(path, FileAttributes.ReadOnly);

        // Act
        Task Fn()
        {
            return skill.WriteAsync(path, "hello world");
        }

        // Assert
        _ = await Assert.ThrowsAsync<UnauthorizedAccessException>(Fn);
    }
}
