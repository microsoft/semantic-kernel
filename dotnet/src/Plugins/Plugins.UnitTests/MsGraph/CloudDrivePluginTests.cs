// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Plugins.MsGraph;
using Moq;
using Xunit;

namespace SemanticKernel.Plugins.UnitTests.MsGraph;

public class CloudDrivePluginTests
{
    [Fact]
    public async Task UploadSmallFileAsyncSucceedsAsync()
    {
        // Arrange
        string allowedDir = Path.GetTempPath();
        string anyFilePath = Path.Combine(allowedDir, Guid.NewGuid().ToString());

        Mock<ICloudDriveConnector> connectorMock = new();
        connectorMock.Setup(c => c.UploadSmallFileAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask);

        CloudDrivePlugin target = new(connectorMock.Object) { AllowedUploadDirectories = [allowedDir] };

        // Act
        await target.UploadFileAsync(anyFilePath, Guid.NewGuid().ToString());

        // Assert
        connectorMock.VerifyAll();
    }

    [Fact]
    public async Task CreateLinkAsyncSucceedsAsync()
    {
        // Arrange
        string anyFilePath = Guid.NewGuid().ToString();
        string anyLink = Guid.NewGuid().ToString();

        Mock<ICloudDriveConnector> connectorMock = new();
        connectorMock.Setup(c => c.CreateShareLinkAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<string>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(anyLink);

        CloudDrivePlugin target = new(connectorMock.Object);

        // Act
        string actual = await target.CreateLinkAsync(anyFilePath);

        // Assert
        Assert.Equal(anyLink, actual);
        connectorMock.VerifyAll();
    }

    [Fact]
    public async Task GetFileContentAsyncSucceedsAsync()
    {
        string anyFilePath = Guid.NewGuid().ToString();
        string expectedContent = Guid.NewGuid().ToString();
        using MemoryStream expectedStream = new(Encoding.UTF8.GetBytes(expectedContent));

        // Arrange
        Mock<ICloudDriveConnector> connectorMock = new();
        connectorMock.Setup(c => c.GetFileContentStreamAsync(It.IsAny<string>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(expectedStream);

        CloudDrivePlugin target = new(connectorMock.Object);

        // Act
        string? actual = await target.GetFileContentAsync(anyFilePath);

        // Assert
        Assert.Equal(expectedContent, actual);
        connectorMock.VerifyAll();
    }

    [Fact]
    public async Task ItDeniesAllPathsByDefaultAsync()
    {
        // Arrange
        string filePath = Path.Combine(Path.GetTempPath(), "somefile.txt");

        Mock<ICloudDriveConnector> connectorMock = new();
        CloudDrivePlugin target = new(connectorMock.Object);

        // Act & Assert — default config denies all paths
        await Assert.ThrowsAsync<InvalidOperationException>(async () =>
            await target.UploadFileAsync(filePath, "/remote.txt"));
    }

    [Fact]
    public async Task ItDeniesPathTraversalAsync()
    {
        // Arrange
        var allowedDir = Path.Combine(Path.GetTempPath(), "allowed-folder");
        var traversalPath = Path.Combine(allowedDir, "..", "outside-folder", "secret.txt");

        Mock<ICloudDriveConnector> connectorMock = new();
        CloudDrivePlugin target = new(connectorMock.Object) { AllowedUploadDirectories = [allowedDir] };

        // Act & Assert — traversal path is canonicalized and rejected
        await Assert.ThrowsAsync<InvalidOperationException>(async () =>
            await target.UploadFileAsync(traversalPath, "/remote.txt"));
    }

    [Fact]
    public async Task ItDeniesUncPathsAsync()
    {
        // Arrange
        Mock<ICloudDriveConnector> connectorMock = new();
        CloudDrivePlugin target = new(connectorMock.Object) { AllowedUploadDirectories = [Path.GetTempPath()] };

        // Act & Assert — UNC paths are rejected (ArgumentException on Windows, InvalidOperationException on Linux
        // where the path is canonicalized differently and fails the allowlist check instead)
        await Assert.ThrowsAnyAsync<Exception>(async () =>
            await target.UploadFileAsync("\\\\UNC\\server\\folder\\file.txt", "/remote.txt"));
    }

    [Fact]
    public async Task ItDeniesDisallowedDirectoriesAsync()
    {
        // Arrange
        var allowedDir = Path.Combine(Path.GetTempPath(), "allowed");
        var disallowedPath = Path.Combine(Path.GetTempPath(), "disallowed", "file.txt");

        Mock<ICloudDriveConnector> connectorMock = new();
        CloudDrivePlugin target = new(connectorMock.Object) { AllowedUploadDirectories = [allowedDir] };

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(async () =>
            await target.UploadFileAsync(disallowedPath, "/remote.txt"));
    }

    [Fact]
    public async Task ItAllowsSubdirectoriesOfAllowedDirectoriesAsync()
    {
        // Arrange
        var allowedDir = Path.GetTempPath();
        var subDirPath = Path.Combine(allowedDir, "subdir", "nested", "file.txt");

        Mock<ICloudDriveConnector> connectorMock = new();
        connectorMock.Setup(c => c.UploadSmallFileAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask);

        CloudDrivePlugin target = new(connectorMock.Object) { AllowedUploadDirectories = [allowedDir] };

        // Act — subdirectory of allowed folder should succeed
        await target.UploadFileAsync(subDirPath, "/remote.txt");

        // Assert
        connectorMock.VerifyAll();
    }

    [Fact]
    public async Task ItExpandsEnvironmentVariablesAndValidatesAsync()
    {
        // Arrange — set a dedicated test env var to avoid platform-specific assumptions
        var tempDir = Path.GetTempPath().TrimEnd(Path.DirectorySeparatorChar);
        var envVarName = "SK_TEST_UPLOAD_DIR";
        var originalValue = Environment.GetEnvironmentVariable(envVarName);
        try
        {
            Environment.SetEnvironmentVariable(envVarName, tempDir);
            var envVarPath = Path.Combine($"%{envVarName}%", "testfile.txt");

            Mock<ICloudDriveConnector> connectorMock = new();
            connectorMock.Setup(c => c.UploadSmallFileAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<CancellationToken>()))
                .Returns(Task.CompletedTask);

            CloudDrivePlugin target = new(connectorMock.Object) { AllowedUploadDirectories = [tempDir] };

            // Act — env var should be expanded and path should be allowed
            await target.UploadFileAsync(envVarPath, "/remote.txt");

            // Assert
            connectorMock.VerifyAll();
        }
        finally
        {
            Environment.SetEnvironmentVariable(envVarName, originalValue);
        }
    }

    [Fact]
    public async Task ItDeniesExpandedEnvironmentVariablePathsOutsideAllowedAsync()
    {
        // Arrange — set a dedicated test env var; allow a subdirectory but env var expands outside it
        var tempDir = Path.GetTempPath().TrimEnd(Path.DirectorySeparatorChar);
        var allowedDir = Path.Combine(tempDir, "specific-allowed");
        var envVarName = "SK_TEST_UPLOAD_DIR";
        var originalValue = Environment.GetEnvironmentVariable(envVarName);
        try
        {
            Environment.SetEnvironmentVariable(envVarName, tempDir);
            var envVarPath = Path.Combine($"%{envVarName}%", "outside-file.txt");

            Mock<ICloudDriveConnector> connectorMock = new();
            CloudDrivePlugin target = new(connectorMock.Object) { AllowedUploadDirectories = [allowedDir] };

            // Act & Assert — expanded path is outside allowed directory
            await Assert.ThrowsAsync<InvalidOperationException>(async () =>
                await target.UploadFileAsync(envVarPath, "/remote.txt"));
        }
        finally
        {
            Environment.SetEnvironmentVariable(envVarName, originalValue);
        }
    }

    [Fact]
    public async Task ItRespectsPlatformCaseSensitivityAsync()
    {
        // Arrange — use differently-cased allowed dir vs file path
        var allowedDir = Path.Combine(Path.GetTempPath(), "AllowedFolder");
        var filePath = Path.Combine(Path.GetTempPath(), "allowedfolder", "file.txt");

        Mock<ICloudDriveConnector> connectorMock = new();
        connectorMock.Setup(c => c.UploadSmallFileAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask);

        CloudDrivePlugin target = new(connectorMock.Object) { AllowedUploadDirectories = [allowedDir] };

        if (RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
        {
            // Windows: case-insensitive FS — differently-cased path should be allowed
            await target.UploadFileAsync(filePath, "/remote.txt");
            connectorMock.VerifyAll();
        }
        else
        {
            // Linux/macOS: case-sensitive FS — differently-cased path should be denied
            await Assert.ThrowsAsync<InvalidOperationException>(async () =>
                await target.UploadFileAsync(filePath, "/remote.txt"));
        }
    }
}
