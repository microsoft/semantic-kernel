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

        CloudDrivePlugin target = new(connectorMock.Object) { AllowedUploadDirectories = [allowedDir], AllowedUploadDestinationPaths = ["/"] };

        // Act
        await target.UploadFileAsync(anyFilePath, "/remote.txt");

        // Assert
        connectorMock.VerifyAll();
    }

    [Fact]
    public async Task CreateLinkAsyncSucceedsAsync()
    {
        // Arrange
        string anyFilePath = "/Documents/report.docx";
        string anyLink = Guid.NewGuid().ToString();

        Mock<ICloudDriveConnector> connectorMock = new();
        connectorMock.Setup(c => c.CreateShareLinkAsync(anyFilePath, "view", "organization", It.IsAny<CancellationToken>()))
            .ReturnsAsync(anyLink);

        CloudDrivePlugin target = new(connectorMock.Object) { AllowedSharePaths = ["/Documents"] };

        // Act
        string actual = await target.CreateLinkAsync(anyFilePath);

        // Assert
        Assert.Equal(anyLink, actual);
        connectorMock.VerifyAll();
    }

    [Fact]
    public async Task CreateLinkAsyncUsesOrganizationScopeAsync()
    {
        // Arrange
        string anyFilePath = "/Documents/report.docx";
        string anyLink = Guid.NewGuid().ToString();

        Mock<ICloudDriveConnector> connectorMock = new();
        connectorMock.Setup(c => c.CreateShareLinkAsync(anyFilePath, "view", "organization", It.IsAny<CancellationToken>()))
            .ReturnsAsync(anyLink);

        CloudDrivePlugin target = new(connectorMock.Object) { AllowedSharePaths = ["/Documents"] };

        // Act
        await target.CreateLinkAsync(anyFilePath);

        // Assert — verify "organization" scope was passed, not "anonymous"
        connectorMock.Verify(c => c.CreateShareLinkAsync(anyFilePath, "view", "organization", It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task CreateLinkAsyncDeniesAllPathsByDefaultAsync()
    {
        // Arrange
        Mock<ICloudDriveConnector> connectorMock = new();
        CloudDrivePlugin target = new(connectorMock.Object);

        // Act & Assert — default config denies all share paths
        await Assert.ThrowsAsync<InvalidOperationException>(async () =>
            await target.CreateLinkAsync("/Documents/secret.docx"));
    }

    [Fact]
    public async Task CreateLinkAsyncDeniesPathsOutsideAllowedAsync()
    {
        // Arrange
        Mock<ICloudDriveConnector> connectorMock = new();
        CloudDrivePlugin target = new(connectorMock.Object) { AllowedSharePaths = ["/Documents/Public"] };

        // Act & Assert — path outside allowed share paths is denied
        await Assert.ThrowsAsync<InvalidOperationException>(async () =>
            await target.CreateLinkAsync("/Confidential/secret.docx"));
    }

    [Fact]
    public async Task CreateLinkAsyncAllowsSubdirectoriesOfAllowedSharePathsAsync()
    {
        // Arrange
        string filePath = "/Documents/Public/Reports/Q1/summary.docx";
        string anyLink = Guid.NewGuid().ToString();

        Mock<ICloudDriveConnector> connectorMock = new();
        connectorMock.Setup(c => c.CreateShareLinkAsync(filePath, "view", "organization", It.IsAny<CancellationToken>()))
            .ReturnsAsync(anyLink);

        CloudDrivePlugin target = new(connectorMock.Object) { AllowedSharePaths = ["/Documents/Public"] };

        // Act — subdirectory of allowed share path should succeed
        string actual = await target.CreateLinkAsync(filePath);

        // Assert
        Assert.Equal(anyLink, actual);
        connectorMock.VerifyAll();
    }

    [Fact]
    public async Task GetFileContentAsyncSucceedsAsync()
    {
        string anyFilePath = "/Documents/report.txt";
        string expectedContent = Guid.NewGuid().ToString();
        using MemoryStream expectedStream = new(Encoding.UTF8.GetBytes(expectedContent));

        // Arrange
        Mock<ICloudDriveConnector> connectorMock = new();
        connectorMock.Setup(c => c.GetFileContentStreamAsync(anyFilePath, It.IsAny<CancellationToken>()))
            .ReturnsAsync(expectedStream);

        CloudDrivePlugin target = new(connectorMock.Object) { AllowedReadPaths = ["/Documents"] };

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
        CloudDrivePlugin target = new(connectorMock.Object) { AllowedUploadDirectories = [allowedDir], AllowedUploadDestinationPaths = ["/"] };
        await Assert.ThrowsAsync<InvalidOperationException>(async () =>
            await target.UploadFileAsync(traversalPath, "/remote.txt"));
    }

    [Fact]
    public async Task ItDeniesUncPathsAsync()
    {
        // Arrange
        Mock<ICloudDriveConnector> connectorMock = new();
        CloudDrivePlugin target = new(connectorMock.Object) { AllowedUploadDirectories = [Path.GetTempPath()], AllowedUploadDestinationPaths = ["/"] };

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
        CloudDrivePlugin target = new(connectorMock.Object) { AllowedUploadDirectories = [allowedDir], AllowedUploadDestinationPaths = ["/"] };

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

        CloudDrivePlugin target = new(connectorMock.Object) { AllowedUploadDirectories = [allowedDir], AllowedUploadDestinationPaths = ["/"] };

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

            CloudDrivePlugin target = new(connectorMock.Object) { AllowedUploadDirectories = [tempDir], AllowedUploadDestinationPaths = ["/"] };

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
            CloudDrivePlugin target = new(connectorMock.Object) { AllowedUploadDirectories = [allowedDir], AllowedUploadDestinationPaths = ["/"] };

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

        CloudDrivePlugin target = new(connectorMock.Object) { AllowedUploadDirectories = [allowedDir], AllowedUploadDestinationPaths = ["/"] };

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

    [Fact]
    public async Task ItDeniesEnvVarExpansionToUncPathAsync()
    {
        // Arrange — env var that expands to a UNC path should be rejected
        var envVarName = "SK_TEST_UNC_" + Guid.NewGuid().ToString("N")[..8];
        var originalValue = Environment.GetEnvironmentVariable(envVarName);

        try
        {
            Environment.SetEnvironmentVariable(envVarName, "\\\\server\\share");
            var maliciousPath = Path.Combine($"%{envVarName}%", "secret.txt");

            Mock<ICloudDriveConnector> connectorMock = new();
            CloudDrivePlugin target = new(connectorMock.Object) { AllowedUploadDirectories = [Path.GetTempPath()], AllowedUploadDestinationPaths = ["/"] };

            // Act & Assert — UNC path after env-var expansion should be rejected
            await Assert.ThrowsAsync<ArgumentException>(async () =>
                await target.UploadFileAsync(maliciousPath, "/remote.txt"));
        }
        finally
        {
            Environment.SetEnvironmentVariable(envVarName, originalValue);
        }
    }

    [Fact]
    public async Task CreateLinkAsyncDeniesPathTraversalAsync()
    {
        // Arrange — path with ".." segments that would bypass the allowed path prefix
        Mock<ICloudDriveConnector> connectorMock = new();
        CloudDrivePlugin target = new(connectorMock.Object) { AllowedSharePaths = ["/Documents"] };

        // Act & Assert — traversal path should be denied even though it string-starts-with /Documents
        await Assert.ThrowsAsync<InvalidOperationException>(async () =>
            await target.CreateLinkAsync("/Documents/../Confidential/secret.docx"));
    }

    [Fact]
    public async Task CreateLinkAsyncDeniesPathTraversalWithSubdirAsync()
    {
        // Arrange — traversal from an allowed subdirectory to an unauthorized location
        Mock<ICloudDriveConnector> connectorMock = new();
        CloudDrivePlugin target = new(connectorMock.Object) { AllowedSharePaths = ["/Documents/Public"] };

        // Act & Assert — traversal should be denied
        await Assert.ThrowsAsync<InvalidOperationException>(async () =>
            await target.CreateLinkAsync("/Documents/Public/../Confidential/secret.docx"));
    }

    [Fact]
    public async Task ItDeniesForwardSlashUncPathsAsync()
    {
        // Arrange — forward-slash UNC paths should also be rejected
        Mock<ICloudDriveConnector> connectorMock = new();
        CloudDrivePlugin target = new(connectorMock.Object) { AllowedUploadDirectories = [Path.GetTempPath()], AllowedUploadDestinationPaths = ["/"] };

        // Act & Assert — forward-slash UNC path is rejected
        await Assert.ThrowsAsync<ArgumentException>(async () =>
            await target.UploadFileAsync("//server/share/file.txt", "/remote.txt"));
    }

    [Fact]
    public async Task ItDeniesEnvVarExpansionToForwardSlashUncPathAsync()
    {
        // Arrange — env var that expands to a forward-slash UNC path should be rejected
        var envVarName = "SK_TEST_FWDUNC_" + Guid.NewGuid().ToString("N")[..8];
        var originalValue = Environment.GetEnvironmentVariable(envVarName);

        try
        {
            Environment.SetEnvironmentVariable(envVarName, "//server/share");
            var maliciousPath = $"%{envVarName}%/secret.txt";

            Mock<ICloudDriveConnector> connectorMock = new();
            CloudDrivePlugin target = new(connectorMock.Object) { AllowedUploadDirectories = [Path.GetTempPath()], AllowedUploadDestinationPaths = ["/"] };

            // Act & Assert — forward-slash UNC path after env-var expansion should be rejected
            await Assert.ThrowsAsync<ArgumentException>(async () =>
                await target.UploadFileAsync(maliciousPath, "/remote.txt"));
        }
        finally
        {
            Environment.SetEnvironmentVariable(envVarName, originalValue);
        }
    }

    [Fact]
    public async Task ItDeniesEnvVarTraversalBypassAsync()
    {
        // Arrange — env var that expands to a traversal path
        var allowedDir = Path.Combine(Path.GetTempPath(), "allowed-sandbox");
        var envVarName = "SK_TEST_TRAV_" + Guid.NewGuid().ToString("N")[..8];
        var originalValue = Environment.GetEnvironmentVariable(envVarName);

        try
        {
            Environment.SetEnvironmentVariable(envVarName,
                $"{Path.DirectorySeparatorChar}..{Path.DirectorySeparatorChar}elsewhere");
            var maliciousPath = Path.Combine(allowedDir, $"%{envVarName}%", "secret.txt");

            Mock<ICloudDriveConnector> connectorMock = new();
            CloudDrivePlugin target = new(connectorMock.Object) { AllowedUploadDirectories = [allowedDir], AllowedUploadDestinationPaths = ["/"] };

            // Act & Assert — after env-var expansion, the canonical path lands outside the allowed directory
            await Assert.ThrowsAsync<InvalidOperationException>(async () =>
                await target.UploadFileAsync(maliciousPath, "/remote.txt"));
        }
        finally
        {
            Environment.SetEnvironmentVariable(envVarName, originalValue);
        }
    }

    [Fact]
    public async Task GetFileContentAsyncDeniesAllPathsByDefaultAsync()
    {
        // Arrange
        Mock<ICloudDriveConnector> connectorMock = new();
        CloudDrivePlugin target = new(connectorMock.Object);

        // Act & Assert — default config denies all read paths
        await Assert.ThrowsAsync<InvalidOperationException>(async () =>
            await target.GetFileContentAsync("/Documents/secret.docx"));
    }

    [Fact]
    public async Task GetFileContentAsyncDeniesPathsOutsideAllowedAsync()
    {
        // Arrange
        Mock<ICloudDriveConnector> connectorMock = new();
        CloudDrivePlugin target = new(connectorMock.Object) { AllowedReadPaths = ["/Documents/Public"] };

        // Act & Assert — path outside allowed read paths is denied
        await Assert.ThrowsAsync<InvalidOperationException>(async () =>
            await target.GetFileContentAsync("/Confidential/secret.docx"));
    }

    [Fact]
    public async Task GetFileContentAsyncDeniesPathTraversalAsync()
    {
        // Arrange
        Mock<ICloudDriveConnector> connectorMock = new();
        CloudDrivePlugin target = new(connectorMock.Object) { AllowedReadPaths = ["/Documents"] };

        // Act & Assert — traversal path should be denied
        await Assert.ThrowsAsync<InvalidOperationException>(async () =>
            await target.GetFileContentAsync("/Documents/../Confidential/secret.docx"));
    }

    [Fact]
    public async Task GetFileContentAsyncAllowsSubdirectoriesOfAllowedReadPathsAsync()
    {
        // Arrange
        string filePath = "/Documents/Public/Reports/Q1/summary.docx";
        string expectedContent = "file content";
        using MemoryStream expectedStream = new(Encoding.UTF8.GetBytes(expectedContent));

        Mock<ICloudDriveConnector> connectorMock = new();
        connectorMock.Setup(c => c.GetFileContentStreamAsync(filePath, It.IsAny<CancellationToken>()))
            .ReturnsAsync(expectedStream);

        CloudDrivePlugin target = new(connectorMock.Object) { AllowedReadPaths = ["/Documents/Public"] };

        // Act
        string? actual = await target.GetFileContentAsync(filePath);

        // Assert
        Assert.Equal(expectedContent, actual);
        connectorMock.VerifyAll();
    }

    [Fact]
    public async Task GetFileContentAsyncDoesNotCallConnectorWhenDeniedAsync()
    {
        // Arrange
        Mock<ICloudDriveConnector> connectorMock = new(MockBehavior.Strict);
        CloudDrivePlugin target = new(connectorMock.Object) { AllowedReadPaths = ["/Documents"] };

        // Act & Assert — connector should never be called for denied paths
        await Assert.ThrowsAsync<InvalidOperationException>(async () =>
            await target.GetFileContentAsync("/Confidential/secret.docx"));
        connectorMock.VerifyNoOtherCalls();
    }

    [Fact]
    public async Task UploadFileAsyncDeniesDisallowedDestinationPathAsync()
    {
        // Arrange
        string allowedDir = Path.GetTempPath();
        string anyFilePath = Path.Combine(allowedDir, Guid.NewGuid().ToString());

        Mock<ICloudDriveConnector> connectorMock = new();
        CloudDrivePlugin target = new(connectorMock.Object)
        {
            AllowedUploadDirectories = [allowedDir],
            AllowedUploadDestinationPaths = ["/Documents/Uploads"]
        };

        // Act & Assert — destination outside allowed paths is denied
        await Assert.ThrowsAsync<InvalidOperationException>(async () =>
            await target.UploadFileAsync(anyFilePath, "/Confidential/secret.docx"));
    }

    [Fact]
    public async Task UploadFileAsyncDeniesAllDestinationPathsByDefaultAsync()
    {
        // Arrange
        string allowedDir = Path.GetTempPath();
        string anyFilePath = Path.Combine(allowedDir, Guid.NewGuid().ToString());

        Mock<ICloudDriveConnector> connectorMock = new();
        CloudDrivePlugin target = new(connectorMock.Object) { AllowedUploadDirectories = [allowedDir] };

        // Act & Assert — default config denies all destination paths
        await Assert.ThrowsAsync<InvalidOperationException>(async () =>
            await target.UploadFileAsync(anyFilePath, "/remote.txt"));
    }

    [Fact]
    public async Task UploadFileAsyncAllowsDestinationInAllowedPathAsync()
    {
        // Arrange
        string allowedDir = Path.GetTempPath();
        string anyFilePath = Path.Combine(allowedDir, Guid.NewGuid().ToString());

        Mock<ICloudDriveConnector> connectorMock = new();
        connectorMock.Setup(c => c.UploadSmallFileAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask);

        CloudDrivePlugin target = new(connectorMock.Object)
        {
            AllowedUploadDirectories = [allowedDir],
            AllowedUploadDestinationPaths = ["/Documents"]
        };

        // Act
        await target.UploadFileAsync(anyFilePath, "/Documents/Uploads/report.txt");

        // Assert
        connectorMock.VerifyAll();
    }

    [Fact]
    public async Task UploadFileAsyncDeniesDestinationPathTraversalAsync()
    {
        // Arrange
        string allowedDir = Path.GetTempPath();
        string anyFilePath = Path.Combine(allowedDir, Guid.NewGuid().ToString());

        Mock<ICloudDriveConnector> connectorMock = new();
        CloudDrivePlugin target = new(connectorMock.Object)
        {
            AllowedUploadDirectories = [allowedDir],
            AllowedUploadDestinationPaths = ["/Documents"]
        };

        // Act & Assert — traversal in destination path should be denied
        await Assert.ThrowsAsync<InvalidOperationException>(async () =>
            await target.UploadFileAsync(anyFilePath, "/Documents/../Confidential/secret.docx"));
    }

    [Fact]
    public async Task UploadFileAsyncDoesNotCallConnectorWhenDestinationDeniedAsync()
    {
        // Arrange
        Mock<ICloudDriveConnector> connectorMock = new(MockBehavior.Strict);
        CloudDrivePlugin target = new(connectorMock.Object)
        {
            AllowedUploadDirectories = [Path.GetTempPath()],
            AllowedUploadDestinationPaths = ["/Documents"]
        };

        // Act & Assert — connector should never be called when destination is denied
        await Assert.ThrowsAsync<InvalidOperationException>(async () =>
            await target.UploadFileAsync(Path.Combine(Path.GetTempPath(), "file.txt"), "/Confidential/secret.docx"));
        connectorMock.VerifyNoOtherCalls();
    }
}
