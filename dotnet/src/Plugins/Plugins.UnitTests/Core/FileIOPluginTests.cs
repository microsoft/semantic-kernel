// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.AccessControl;
using System.Security.Principal;
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
    public async Task ItDoesNotRevealReadOnlyOrExistenceOfDisallowedFilesAsync()
    {
        // Arrange
        var tempDir = Path.Combine(Path.GetTempPath(), $"FileIOPluginTests_{Guid.NewGuid():N}");
        var allowedDir = Path.Combine(tempDir, "allowed");
        var outsideDir = Path.Combine(tempDir, "outside");
        Directory.CreateDirectory(allowedDir);
        Directory.CreateDirectory(outsideDir);

        var readOnlyFile = Path.Combine(outsideDir, "readonly.txt");
        var missingFile = Path.Combine(outsideDir, "missing.txt");
        await File.WriteAllTextAsync(readOnlyFile, "secret");
        File.SetAttributes(readOnlyFile, FileAttributes.ReadOnly);

        try
        {
            foreach (var plugin in new[]
            {
                new FileIOPlugin(),
                new FileIOPlugin() { AllowedFolders = [allowedDir], DisableFileOverwrite = false }
            })
            {
                // Act
                var readOnlyReadEx = await Assert.ThrowsAsync<InvalidOperationException>(() => plugin.ReadAsync(readOnlyFile));
                var missingReadEx = await Assert.ThrowsAsync<InvalidOperationException>(() => plugin.ReadAsync(missingFile));
                var readOnlyWriteEx = await Assert.ThrowsAsync<InvalidOperationException>(() => plugin.WriteAsync(readOnlyFile, "changed"));
                var missingWriteEx = await Assert.ThrowsAsync<InvalidOperationException>(() => plugin.WriteAsync(missingFile, "changed"));

                // Assert - responses for existing read-only and missing files must be indistinguishable
                Assert.Equal(missingReadEx.Message, readOnlyReadEx.Message);
                Assert.Equal(missingWriteEx.Message, readOnlyWriteEx.Message);
                Assert.DoesNotContain(outsideDir, readOnlyReadEx.Message, StringComparison.OrdinalIgnoreCase);
                Assert.DoesNotContain(outsideDir, readOnlyWriteEx.Message, StringComparison.OrdinalIgnoreCase);
            }
        }
        finally
        {
            File.SetAttributes(readOnlyFile, FileAttributes.Normal);
            TryDeleteDirectory(tempDir);
        }
    }

    [Fact]
    public async Task ItDoesNotIncludePathInReadOnlyExceptionAsync()
    {
        // Arrange
        var plugin = new FileIOPlugin()
        {
            AllowedFolders = [Path.GetTempPath()],
            DisableFileOverwrite = false
        };
        var path = Path.GetTempFileName();
        File.SetAttributes(path, FileAttributes.ReadOnly);

        try
        {
            // Act
            var ex = await Assert.ThrowsAsync<UnauthorizedAccessException>(() => plugin.WriteAsync(path, "hello world"));

            // Assert
            Assert.DoesNotContain(Path.GetFileName(path), ex.Message, StringComparison.OrdinalIgnoreCase);
        }
        finally
        {
            File.SetAttributes(path, FileAttributes.Normal);
            File.Delete(path);
        }
    }

    [Fact]
    public async Task ItDeniesUnresolvablePathsWithoutHidingConfigurationErrorsAsync()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"FileIOPluginTests_{Guid.NewGuid():N}");
        var allowedDir = Path.Combine(tempDir, "allowed");
        var outsideDir = Path.Combine(tempDir, "outside");
        Directory.CreateDirectory(allowedDir);
        Directory.CreateDirectory(outsideDir);
        var linkPath = Path.Combine(outsideDir, "loop");

        try
        {
            try
            {
                Directory.CreateSymbolicLink(linkPath, linkPath);
            }
            catch (Exception ex) when (ex is IOException or UnauthorizedAccessException)
            {
                // Skip if this environment does not permit symbolic link creation.
                return;
            }

            var resolutionError = Assert.Throws<InvalidOperationException>(() => PathUtilities.GetSafeFullPath(linkPath));
            var plugin = new FileIOPlugin() { AllowedFolders = [allowedDir] };
            var missingPath = Path.Combine(outsideDir, "missing.txt");
            var unresolvablePath = Path.Combine(linkPath, "file.txt");

            var expectedReadError = await Assert.ThrowsAsync<InvalidOperationException>(() => plugin.ReadAsync(missingPath));
            var expectedWriteError = await Assert.ThrowsAsync<InvalidOperationException>(() => plugin.WriteAsync(missingPath, "changed"));
            var readError = await Assert.ThrowsAsync<InvalidOperationException>(() => plugin.ReadAsync(unresolvablePath));
            var writeError = await Assert.ThrowsAsync<InvalidOperationException>(() => plugin.WriteAsync(unresolvablePath, "changed"));

            Assert.Equal(expectedReadError.Message, readError.Message);
            Assert.Equal(expectedWriteError.Message, writeError.Message);

            plugin.AllowedFolders = [linkPath];
            var regularPath = Path.Combine(allowedDir, "missing.txt");
            var configurationReadError = await Assert.ThrowsAsync<InvalidOperationException>(() => plugin.ReadAsync(regularPath));
            var configurationWriteError = await Assert.ThrowsAsync<InvalidOperationException>(() => plugin.WriteAsync(regularPath, "changed"));
            Assert.Equal(resolutionError.Message, configurationReadError.Message);
            Assert.Equal(resolutionError.Message, configurationWriteError.Message);
        }
        finally
        {
            TryDeleteDirectory(tempDir);
        }
    }

    [Fact]
    public async Task ItDeniesInaccessiblePathsWithoutHidingConfigurationErrorsAsync()
    {
        if (!OperatingSystem.IsWindows())
        {
            return;
        }

        var tempDir = Path.Combine(Path.GetTempPath(), $"FileIOPluginTests_{Guid.NewGuid():N}");
        var allowedDir = Path.Combine(tempDir, "allowed");
        var outsideDir = Path.Combine(tempDir, "outside");
        Directory.CreateDirectory(allowedDir);
        Directory.CreateDirectory(outsideDir);
        var restrictedDir = Directory.CreateDirectory(Path.Combine(outsideDir, "restricted"));
        var restrictedRoot = Directory.CreateDirectory(Path.Combine(restrictedDir.FullName, "nested"));
        var inaccessiblePath = Path.Combine(restrictedRoot.FullName, "file.txt");
        await File.WriteAllTextAsync(inaccessiblePath, "secret");

        var restrictedSecurity = restrictedDir.GetAccessControl(AccessControlSections.Access);
        using var identity = WindowsIdentity.GetCurrent();
        Assert.NotNull(identity.User);
        var denyRule = new FileSystemAccessRule(
            identity.User,
            FileSystemRights.Read,
            InheritanceFlags.ContainerInherit | InheritanceFlags.ObjectInherit,
            PropagationFlags.None,
            AccessControlType.Deny);
        restrictedSecurity.AddAccessRule(denyRule);

        try
        {
            restrictedDir.SetAccessControl(restrictedSecurity);
            Assert.Throws<UnauthorizedAccessException>(() => PathUtilities.GetSafeFullPath(inaccessiblePath));
            var plugin = new FileIOPlugin() { AllowedFolders = [allowedDir] };
            var missingPath = Path.Combine(outsideDir, "missing.txt");

            var expectedReadError = await Assert.ThrowsAsync<InvalidOperationException>(() => plugin.ReadAsync(missingPath));
            var expectedWriteError = await Assert.ThrowsAsync<InvalidOperationException>(() => plugin.WriteAsync(missingPath, "changed"));
            var readError = await Assert.ThrowsAsync<InvalidOperationException>(() => plugin.ReadAsync(inaccessiblePath));
            var writeError = await Assert.ThrowsAsync<InvalidOperationException>(() => plugin.WriteAsync(inaccessiblePath, "changed"));

            Assert.Equal(expectedReadError.Message, readError.Message);
            Assert.Equal(expectedWriteError.Message, writeError.Message);

            plugin.AllowedFolders = [restrictedRoot.FullName];
            var regularPath = Path.Combine(allowedDir, "missing.txt");
            await Assert.ThrowsAsync<UnauthorizedAccessException>(() => plugin.ReadAsync(regularPath));
            await Assert.ThrowsAsync<UnauthorizedAccessException>(() => plugin.WriteAsync(regularPath, "changed"));
        }
        finally
        {
            restrictedSecurity.RemoveAccessRule(denyRule);
            restrictedDir.SetAccessControl(restrictedSecurity);
            TryDeleteDirectory(tempDir);
        }
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
    [InlineData("\\\\UNC\\server\\folder\\myfile.txt")]
    [InlineData("//UNC/server/folder/myfile.txt")]
    [InlineData("/\\UNC\\server\\folder\\myfile.txt")]
    [InlineData("\\/UNC/server/folder/myfile.txt")]
    public async Task ItRejectsUncOrExtendedPathsOnReadAsync(string path)
    {
        // Arrange
        var plugin = new FileIOPlugin()
        {
            AllowedFolders = [Path.GetTempPath()]
        };

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentException>(() => plugin.ReadAsync(path));
    }

    [Theory]
    [InlineData("\\\\UNC\\server\\folder\\myfile.txt")]
    [InlineData("//UNC/server/folder/myfile.txt")]
    [InlineData("/\\UNC\\server\\folder\\myfile.txt")]
    [InlineData("\\/UNC/server/folder/myfile.txt")]
    public async Task ItRejectsUncOrExtendedPathsOnWriteAsync(string path)
    {
        // Arrange
        var plugin = new FileIOPlugin()
        {
            AllowedFolders = [Path.GetTempPath()],
            DisableFileOverwrite = false
        };

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentException>(() => plugin.WriteAsync(path, "hello world"));
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
