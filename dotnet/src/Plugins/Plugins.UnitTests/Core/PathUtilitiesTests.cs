// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.Plugins.UnitTests.Core;

public sealed class PathUtilitiesTests : IDisposable
{
    private readonly string _tempDir;

    public PathUtilitiesTests()
    {
        this._tempDir = Path.Combine(Path.GetTempPath(), $"PathUtilitiesTests_{Guid.NewGuid():N}");
        Directory.CreateDirectory(this._tempDir);
    }

    [Fact]
    public void GetSafeFullPathReturnsCanonicalPathForRegularFile()
    {
        // Arrange
        var filePath = Path.Combine(this._tempDir, "regular.txt");
        File.WriteAllText(filePath, "test");

        // Act
        var resolved = PathUtilities.GetSafeFullPath(filePath);

        // Assert
        Assert.Equal(Path.GetFullPath(filePath), resolved);
    }

    [Fact]
    public void GetSafeFullPathResolvesRelativePaths()
    {
        // Arrange
        var filePath = Path.Combine(this._tempDir, "subdir", "..", "regular.txt");
        var expectedPath = Path.GetFullPath(Path.Combine(this._tempDir, "regular.txt"));
        File.WriteAllText(expectedPath, "test");

        // Act
        var resolved = PathUtilities.GetSafeFullPath(filePath);

        // Assert
        Assert.Equal(expectedPath, resolved);
    }

    [Fact]
    public void GetSafeFullPathHandlesNonExistentFile()
    {
        // Arrange
        var filePath = Path.Combine(this._tempDir, "nonexistent.txt");

        // Act
        var resolved = PathUtilities.GetSafeFullPath(filePath);

        // Assert
        Assert.Equal(Path.GetFullPath(filePath), resolved);
    }

    [Fact]
    public void GetSafeFullPathResolvesFileSymlink()
    {
        // Arrange
        var targetFile = Path.Combine(this._tempDir, "target.txt");
        File.WriteAllText(targetFile, "secret content");

        var symlinkPath = Path.Combine(this._tempDir, "link.txt");

        try
        {
            File.CreateSymbolicLink(symlinkPath, targetFile);
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException)
        {
            // Skip: this environment does not permit symbolic link creation (e.g., Windows without the required privilege).
            return;
        }

        // Act
        var resolved = PathUtilities.GetSafeFullPath(symlinkPath);

        // Assert — should resolve to the actual target, not the symlink path
        Assert.Equal(Path.GetFullPath(targetFile), resolved);
    }

    [Fact]
    public void GetSafeFullPathResolvesSymlinkPointingOutsideDirectory()
    {
        // Arrange - simulates the attack scenario:
        // An allowed directory contains a symlink pointing to a file outside it
        var allowedDir = Path.Combine(this._tempDir, "allowed");
        var outsideDir = Path.Combine(this._tempDir, "outside");
        Directory.CreateDirectory(allowedDir);
        Directory.CreateDirectory(outsideDir);

        var sensitiveFile = Path.Combine(outsideDir, "sensitive.txt");
        File.WriteAllText(sensitiveFile, "sensitive data");

        var symlinkInAllowedDir = Path.Combine(allowedDir, "link.txt");

        try
        {
            File.CreateSymbolicLink(symlinkInAllowedDir, sensitiveFile);
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException)
        {
            // Skip: this environment does not permit symbolic link creation (e.g., Windows without the required privilege).
            return;
        }

        // Act
        var resolved = PathUtilities.GetSafeFullPath(symlinkInAllowedDir);

        // Assert — resolved path should be OUTSIDE the allowed directory
        // This proves the symlink bypass is prevented
        var allowedDirCanonical = Path.GetFullPath(allowedDir) + Path.DirectorySeparatorChar;
        Assert.False(resolved.StartsWith(allowedDirCanonical, StringComparison.OrdinalIgnoreCase),
            $"Resolved path '{resolved}' should NOT start with allowed dir '{allowedDirCanonical}'. " +
            "If it does, the symlink bypass vulnerability is still present.");
        Assert.Equal(Path.GetFullPath(sensitiveFile), resolved);
    }

    [Fact]
    public void GetSafeFullPathResolvesDirectorySymlink()
    {
        // Arrange - symlink directory inside allowed dir points to outside
        var allowedDir = Path.Combine(this._tempDir, "allowed");
        var outsideDir = Path.Combine(this._tempDir, "outside");
        Directory.CreateDirectory(allowedDir);
        Directory.CreateDirectory(outsideDir);

        File.WriteAllText(Path.Combine(outsideDir, "secret.txt"), "secret");

        var symlinkDir = Path.Combine(allowedDir, "linkeddir");

        try
        {
            Directory.CreateSymbolicLink(symlinkDir, outsideDir);
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException)
        {
            // Skip: this environment does not permit symbolic link creation (e.g., Windows without the required privilege).
            return;
        }

        var fileViaSymlink = Path.Combine(symlinkDir, "secret.txt");

        // Act
        var resolved = PathUtilities.GetSafeFullPath(fileViaSymlink);

        // Assert — resolved path should point to the real location outside allowed dir
        var expectedPath = Path.GetFullPath(Path.Combine(outsideDir, "secret.txt"));
        Assert.Equal(expectedPath, resolved);
    }

    [Fact]
    public void GetSafeFullPathResolvesNestedDirectorySymlink()
    {
        // Arrange
        var allowedDir = Path.Combine(this._tempDir, "allowed");
        var outsideDir = Path.Combine(this._tempDir, "outside");
        var nestedOutsideDir = Path.Combine(outsideDir, "nested");
        Directory.CreateDirectory(allowedDir);
        Directory.CreateDirectory(nestedOutsideDir);

        File.WriteAllText(Path.Combine(nestedOutsideDir, "secret.txt"), "secret");

        var symlinkDir = Path.Combine(allowedDir, "linkeddir");

        try
        {
            Directory.CreateSymbolicLink(symlinkDir, outsideDir);
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException)
        {
            // Skip: this environment does not permit symbolic link creation (e.g., Windows without the required privilege).
            return;
        }

        var fileViaNestedSymlink = Path.Combine(symlinkDir, "nested", "secret.txt");

        // Act
        var resolved = PathUtilities.GetSafeFullPath(fileViaNestedSymlink);

        // Assert
        var expectedPath = Path.GetFullPath(Path.Combine(nestedOutsideDir, "secret.txt"));
        Assert.Equal(expectedPath, resolved);
    }

    [Fact]
    public void GetSafeFullPathResolvesChainedSymlinks()
    {
        // Arrange - link1 -> link2 -> realTarget
        var realTarget = Path.Combine(this._tempDir, "real.txt");
        File.WriteAllText(realTarget, "secret content");

        var link2 = Path.Combine(this._tempDir, "link2.txt");
        var link1 = Path.Combine(this._tempDir, "link1.txt");

        try
        {
            File.CreateSymbolicLink(link2, realTarget);
            File.CreateSymbolicLink(link1, link2);
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException)
        {
            // Skip: this environment does not permit symbolic link creation (e.g., Windows without the required privilege).
            return;
        }

        // Act
        var resolved = PathUtilities.GetSafeFullPath(link1);

        // Assert — should resolve through the whole chain to the real target
        Assert.Equal(Path.GetFullPath(realTarget), resolved);
    }

    [Fact]
    public void GetSafeFullPathResolvesDanglingSymlinkTarget()
    {
        // Arrange
        var missingTarget = Path.Combine(this._tempDir, "missing.txt");
        var symlinkPath = Path.Combine(this._tempDir, "dangling-link.txt");

        try
        {
            File.CreateSymbolicLink(symlinkPath, missingTarget);
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException)
        {
            // Skip: this environment does not permit symbolic link creation (e.g., Windows without the required privilege).
            return;
        }

        // Act
        var resolved = PathUtilities.GetSafeFullPath(symlinkPath);

        // Assert
        Assert.Equal(Path.GetFullPath(missingTarget), resolved);
    }

    public void Dispose()
    {
        try
        {
            Directory.Delete(this._tempDir, recursive: true);
        }
        catch (IOException)
        {
            // Best effort cleanup
        }
        catch (UnauthorizedAccessException)
        {
            // Best effort cleanup
        }
    }
}
