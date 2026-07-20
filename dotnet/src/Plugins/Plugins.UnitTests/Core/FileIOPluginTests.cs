// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Runtime.InteropServices;
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
        var plugin = new FileIOPlugin() { AllowedFolders = [Path.GetTempPath()] };
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
        var plugin = new FileIOPlugin() { AllowedFolders = [Path.GetTempPath()] };
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
        var plugin = new FileIOPlugin()
        {
            AllowedFolders = [Path.GetTempPath()],
            DisableFileOverwrite = false
        };
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
        var plugin = new FileIOPlugin()
        {
            AllowedFolders = [Path.GetTempPath()],
            DisableFileOverwrite = false
        };
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
    public async Task ItDeniesAllPathsWithDefaultConfigAsync()
    {
        // Arrange
        var plugin = new FileIOPlugin();
        var path = Path.GetTempFileName();

        // Act & Assert - default config denies all paths
        await Assert.ThrowsAsync<InvalidOperationException>(async () => await plugin.ReadAsync(path));
        await Assert.ThrowsAsync<InvalidOperationException>(async () => await plugin.WriteAsync(path, "hello world"));
    }

    [Fact]
    public async Task ItCannotWriteToDisallowedFoldersAsync()
    {
        // Arrange
        var plugin = new FileIOPlugin()
        {
            AllowedFolders = [Path.GetTempPath()],
            DisableFileOverwrite = false
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

    [Theory]
    [InlineData("\\\\server\\share\\file.txt")]
    [InlineData("//server/share/file.txt")]
    [InlineData("\\/server\\share\\file.txt")]
    [InlineData("/\\server/share/file.txt")]
    public async Task ItCannotReadFromUncPathsAsync(string uncPath)
    {
        // Arrange
        var plugin = new FileIOPlugin() { AllowedFolders = [Path.GetTempPath()] };

        // Act
        var exception = await Assert.ThrowsAsync<ArgumentException>(() => plugin.ReadAsync(uncPath));

        // Assert - the UNC guard (not another validation) must be what rejected the path
        Assert.Contains("UNC paths are not supported", exception.Message, StringComparison.Ordinal);
    }

    [Theory]
    [InlineData("\\\\server\\share\\file.txt")]
    [InlineData("//server/share/file.txt")]
    [InlineData("\\/server\\share\\file.txt")]
    [InlineData("/\\server/share/file.txt")]
    public async Task ItCannotWriteToUncPathsAsync(string uncPath)
    {
        // Arrange
        var plugin = new FileIOPlugin()
        {
            AllowedFolders = [Path.GetTempPath()],
            DisableFileOverwrite = false
        };

        // Act
        var exception = await Assert.ThrowsAsync<ArgumentException>(() => plugin.WriteAsync(uncPath, "hello world"));

        // Assert - the UNC guard (not another validation) must be what rejected the path
        Assert.Contains("UNC paths are not supported", exception.Message, StringComparison.Ordinal);
    }

    [Fact]
    public async Task ItCannotReadThroughSymlinkOutsideAllowedFoldersAsync()
    {
        // Arrange
        var tempDir = Path.Combine(Path.GetTempPath(), $"FileIOPluginTests_{Guid.NewGuid():N}");
        var allowedDir = Path.Combine(tempDir, "allowed");
        var outsideDir = Path.Combine(tempDir, "outside");
        Directory.CreateDirectory(allowedDir);
        Directory.CreateDirectory(outsideDir);

        try
        {
            var outsideFile = Path.Combine(outsideDir, "secret.txt");
            await File.WriteAllTextAsync(outsideFile, "secret");

            var symlinkPath = Path.Combine(allowedDir, "link.txt");
            try
            {
                File.CreateSymbolicLink(symlinkPath, outsideFile);
            }
            catch (Exception ex) when (ex is IOException or UnauthorizedAccessException)
            {
                // Skip: this environment does not permit symbolic link creation (e.g., Windows without the required privilege).
                return;
            }

            var plugin = new FileIOPlugin() { AllowedFolders = [allowedDir] };

            // Act & Assert
            await Assert.ThrowsAsync<InvalidOperationException>(() => plugin.ReadAsync(symlinkPath));
        }
        finally
        {
            TryDeleteDirectory(tempDir);
        }
    }

    [Fact]
    public async Task ItCannotWriteThroughSymlinkOutsideAllowedFoldersAsync()
    {
        // Arrange
        var tempDir = Path.Combine(Path.GetTempPath(), $"FileIOPluginTests_{Guid.NewGuid():N}");
        var allowedDir = Path.Combine(tempDir, "allowed");
        var outsideDir = Path.Combine(tempDir, "outside");
        Directory.CreateDirectory(allowedDir);
        Directory.CreateDirectory(outsideDir);

        try
        {
            var outsideFile = Path.Combine(outsideDir, "secret.txt");
            await File.WriteAllTextAsync(outsideFile, "secret");

            var symlinkPath = Path.Combine(allowedDir, "link.txt");
            try
            {
                File.CreateSymbolicLink(symlinkPath, outsideFile);
            }
            catch (Exception ex) when (ex is IOException or UnauthorizedAccessException)
            {
                // Skip: this environment does not permit symbolic link creation (e.g., Windows without the required privilege).
                return;
            }

            var plugin = new FileIOPlugin()
            {
                AllowedFolders = [allowedDir],
                DisableFileOverwrite = false
            };

            // Act & Assert
            await Assert.ThrowsAsync<InvalidOperationException>(() => plugin.WriteAsync(symlinkPath, "changed"));
            Assert.Equal("secret", await File.ReadAllTextAsync(outsideFile));
        }
        finally
        {
            TryDeleteDirectory(tempDir);
        }
    }

    [Fact]
    public async Task ItCannotWriteThroughDanglingSymlinkOutsideAllowedFoldersAsync()
    {
        // Arrange
        var tempDir = Path.Combine(Path.GetTempPath(), $"FileIOPluginTests_{Guid.NewGuid():N}");
        var allowedDir = Path.Combine(tempDir, "allowed");
        var outsideDir = Path.Combine(tempDir, "outside");
        Directory.CreateDirectory(allowedDir);
        Directory.CreateDirectory(outsideDir);

        try
        {
            var outsideFile = Path.Combine(outsideDir, "created-through-link.txt");
            var symlinkPath = Path.Combine(allowedDir, "link.txt");
            try
            {
                File.CreateSymbolicLink(symlinkPath, outsideFile);
            }
            catch (Exception ex) when (ex is IOException or UnauthorizedAccessException)
            {
                // Skip: this environment does not permit symbolic link creation (e.g., Windows without the required privilege).
                return;
            }

            var plugin = new FileIOPlugin()
            {
                AllowedFolders = [allowedDir],
                DisableFileOverwrite = false
            };

            // Act & Assert
            await Assert.ThrowsAsync<InvalidOperationException>(() => plugin.WriteAsync(symlinkPath, "created"));
            Assert.False(File.Exists(outsideFile));
        }
        finally
        {
            TryDeleteDirectory(tempDir);
        }
    }

    [Fact]
    public async Task ItUsesCaseSensitiveAllowListComparisonOnLinuxAsync()
    {
        if (!RuntimeInformation.IsOSPlatform(OSPlatform.Linux))
        {
            return;
        }

        // Arrange
        var tempDir = Path.Combine(Path.GetTempPath(), $"FileIOPluginTests_{Guid.NewGuid():N}");
        var allowedDir = Path.Combine(tempDir, "Allowed");
        var disallowedDir = Path.Combine(tempDir, "allowed");
        Directory.CreateDirectory(allowedDir);
        Directory.CreateDirectory(disallowedDir);

        try
        {
            var disallowedFile = Path.Combine(disallowedDir, "secret.txt");
            await File.WriteAllTextAsync(disallowedFile, "secret");

            var plugin = new FileIOPlugin() { AllowedFolders = [allowedDir] };

            // Act & Assert
            await Assert.ThrowsAsync<InvalidOperationException>(() => plugin.ReadAsync(disallowedFile));
        }
        finally
        {
            TryDeleteDirectory(tempDir);
        }
    }

    private static void TryDeleteDirectory(string path)
    {
        try
        {
            Directory.Delete(path, recursive: true);
        }
        catch (IOException)
        {
        }
        catch (UnauthorizedAccessException)
        {
        }
    }
}
