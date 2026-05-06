// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Plugins.Document;
using Microsoft.SemanticKernel.Plugins.Document.FileSystem;
using Moq;
using Xunit;

namespace SemanticKernel.Plugins.UnitTests.Document;

public class DocumentPluginTests
{
    [Fact]
    public async Task ReadTextAsyncSucceedsAsync()
    {
        // Arrange
        var expectedText = Guid.NewGuid().ToString();
        var folderPath = Path.GetTempPath();
        var anyFilePath = Path.Combine(folderPath, Guid.NewGuid().ToString());

        var fileSystemConnectorMock = new Mock<IFileSystemConnector>();
        fileSystemConnectorMock
            .Setup(mock => mock.GetFileContentStreamAsync(It.Is<string>(filePath => filePath.Equals(anyFilePath, StringComparison.Ordinal)),
                It.IsAny<CancellationToken>()))
            .ReturnsAsync(Stream.Null);

        var documentConnectorMock = new Mock<IDocumentConnector>();
        documentConnectorMock
            .Setup(mock => mock.ReadText(It.IsAny<Stream>()))
            .Returns(expectedText);

        var target = new DocumentPlugin(documentConnectorMock.Object, fileSystemConnectorMock.Object)
        {
            AllowedDirectories = [folderPath]
        };

        // Act
        string actual = await target.ReadTextAsync(anyFilePath);

        // Assert
        Assert.Equal(expectedText, actual);
        fileSystemConnectorMock.VerifyAll();
        documentConnectorMock.VerifyAll();
    }

    [Fact]
    public async Task AppendTextAsyncFileExistsSucceedsAsync()
    {
        // Arrange
        var anyText = Guid.NewGuid().ToString();
        var folderPath = Path.GetTempPath();
        var anyFilePath = Path.Combine(folderPath, Guid.NewGuid().ToString());

        var fileSystemConnectorMock = new Mock<IFileSystemConnector>();
        fileSystemConnectorMock
            .Setup(mock => mock.FileExistsAsync(It.Is<string>(filePath => filePath.Equals(anyFilePath, StringComparison.Ordinal)),
                It.IsAny<CancellationToken>()))
            .ReturnsAsync(true);
        fileSystemConnectorMock
            .Setup(mock => mock.GetWriteableFileStreamAsync(It.Is<string>(filePath => filePath.Equals(anyFilePath, StringComparison.Ordinal)),
                It.IsAny<CancellationToken>()))
            .ReturnsAsync(Stream.Null);

        var documentConnectorMock = new Mock<IDocumentConnector>();
        documentConnectorMock
            .Setup(mock => mock.AppendText(It.IsAny<Stream>(), It.Is<string>(text => text.Equals(anyText, StringComparison.Ordinal))));

        var target = new DocumentPlugin(documentConnectorMock.Object, fileSystemConnectorMock.Object)
        {
            AllowedDirectories = [folderPath]
        };

        // Act
        await target.AppendTextAsync(anyText, anyFilePath);

        // Assert
        fileSystemConnectorMock.VerifyAll();
        documentConnectorMock.VerifyAll();
    }

    [Fact]
    public async Task AppendTextAsyncFileDoesNotExistSucceedsAsync()
    {
        // Arrange
        var anyText = Guid.NewGuid().ToString();
        var folderPath = Path.GetTempPath();
        var anyFilePath = Path.Combine(folderPath, Guid.NewGuid().ToString());

        var fileSystemConnectorMock = new Mock<IFileSystemConnector>();
        fileSystemConnectorMock
            .Setup(mock => mock.FileExistsAsync(It.Is<string>(filePath => filePath.Equals(anyFilePath, StringComparison.Ordinal)),
                It.IsAny<CancellationToken>()))
            .ReturnsAsync(false);
        fileSystemConnectorMock
            .Setup(mock => mock.CreateFileAsync(It.Is<string>(filePath => filePath.Equals(anyFilePath, StringComparison.Ordinal)),
                It.IsAny<CancellationToken>()))
            .ReturnsAsync(Stream.Null);

        var documentConnectorMock = new Mock<IDocumentConnector>();
        documentConnectorMock
            .Setup(mock => mock.Initialize(It.IsAny<Stream>()));
        documentConnectorMock
            .Setup(mock => mock.AppendText(It.IsAny<Stream>(), It.Is<string>(text => text.Equals(anyText, StringComparison.Ordinal))));

        var target = new DocumentPlugin(documentConnectorMock.Object, fileSystemConnectorMock.Object)
        {
            AllowedDirectories = [folderPath]
        };

        // Act
        await target.AppendTextAsync(anyText, anyFilePath);

        // Assert
        fileSystemConnectorMock.VerifyAll();
        documentConnectorMock.VerifyAll();
    }

    [Fact]
    public async Task AppendTextAsyncNoFilePathFailsAsync()
    {
        // Arrange
        var anyText = Guid.NewGuid().ToString();

        var fileSystemConnectorMock = new Mock<IFileSystemConnector>();
        var documentConnectorMock = new Mock<IDocumentConnector>();

        var target = new DocumentPlugin(documentConnectorMock.Object, fileSystemConnectorMock.Object);

        // Act/Assert
        await Assert.ThrowsAnyAsync<ArgumentException>(() =>
           target.AppendTextAsync(anyText, null!));

        // Assert
        fileSystemConnectorMock.Verify(mock => mock.GetWriteableFileStreamAsync(It.IsAny<string>(), It.IsAny<CancellationToken>()), Times.Never());
        documentConnectorMock.Verify(mock => mock.AppendText(It.IsAny<Stream>(), It.IsAny<string>()), Times.Never());
    }

    [Fact]
    public async Task ItDeniesAllPathsWithDefaultConfigAsync()
    {
        // Arrange
        var fileSystemConnectorMock = new Mock<IFileSystemConnector>();
        var documentConnectorMock = new Mock<IDocumentConnector>();
        var target = new DocumentPlugin(documentConnectorMock.Object, fileSystemConnectorMock.Object);

        var filePath = Path.Combine(Path.GetTempPath(), "test.docx");

        // Act & Assert — default config denies all paths
        await Assert.ThrowsAsync<InvalidOperationException>(async () => await target.ReadTextAsync(filePath));
        await Assert.ThrowsAsync<InvalidOperationException>(async () => await target.AppendTextAsync("text", filePath));
    }

    [Fact]
    public async Task ItDeniesPathTraversalAsync()
    {
        // Arrange
        var folderPath = Path.Combine(Path.GetTempPath(), "allowed-folder");
        var traversalPath = Path.Combine(folderPath, "..", "outside-folder", "secret.docx");

        var fileSystemConnectorMock = new Mock<IFileSystemConnector>();
        var documentConnectorMock = new Mock<IDocumentConnector>();
        var target = new DocumentPlugin(documentConnectorMock.Object, fileSystemConnectorMock.Object)
        {
            AllowedDirectories = [folderPath]
        };

        // Act & Assert — traversal path is canonicalized and rejected
        await Assert.ThrowsAsync<InvalidOperationException>(async () => await target.ReadTextAsync(traversalPath));
        await Assert.ThrowsAsync<InvalidOperationException>(async () => await target.AppendTextAsync("text", traversalPath));
    }

    [Fact]
    public async Task ItDeniesUncPathsAsync()
    {
        // Arrange
        var fileSystemConnectorMock = new Mock<IFileSystemConnector>();
        var documentConnectorMock = new Mock<IDocumentConnector>();
        var target = new DocumentPlugin(documentConnectorMock.Object, fileSystemConnectorMock.Object)
        {
            AllowedDirectories = [Path.GetTempPath()]
        };

        // Act & Assert — UNC paths are rejected
        await Assert.ThrowsAnyAsync<Exception>(async () => await target.ReadTextAsync("\\\\UNC\\server\\folder\\file.docx"));
        await Assert.ThrowsAnyAsync<Exception>(async () => await target.AppendTextAsync("text", "\\\\UNC\\server\\folder\\file.docx"));
    }

    [Fact]
    public async Task ItDeniesDisallowedFoldersAsync()
    {
        // Arrange
        var allowedFolder = Path.Combine(Path.GetTempPath(), "allowed");
        var disallowedPath = Path.Combine(Path.GetTempPath(), "disallowed", "file.docx");

        var fileSystemConnectorMock = new Mock<IFileSystemConnector>();
        var documentConnectorMock = new Mock<IDocumentConnector>();
        var target = new DocumentPlugin(documentConnectorMock.Object, fileSystemConnectorMock.Object)
        {
            AllowedDirectories = [allowedFolder]
        };

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(async () => await target.ReadTextAsync(disallowedPath));
        await Assert.ThrowsAsync<InvalidOperationException>(async () => await target.AppendTextAsync("text", disallowedPath));
    }

    [Fact]
    public async Task ItAllowsSubdirectoriesOfAllowedFoldersAsync()
    {
        // Arrange
        var allowedFolder = Path.GetTempPath();
        var subDirPath = Path.Combine(allowedFolder, "subdir", "nested", "file.docx");

        var fileSystemConnectorMock = new Mock<IFileSystemConnector>();
        fileSystemConnectorMock
            .Setup(mock => mock.GetFileContentStreamAsync(It.IsAny<string>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(Stream.Null);

        var documentConnectorMock = new Mock<IDocumentConnector>();
        documentConnectorMock
            .Setup(mock => mock.ReadText(It.IsAny<Stream>()))
            .Returns("content");

        var target = new DocumentPlugin(documentConnectorMock.Object, fileSystemConnectorMock.Object)
        {
            AllowedDirectories = [allowedFolder]
        };

        // Act — subdirectory of allowed folder should succeed
        string result = await target.ReadTextAsync(subDirPath);

        // Assert
        Assert.Equal("content", result);
    }

    [Fact]
    public async Task ItDeniesRelativePathsAsync()
    {
        // Arrange — use a unique subfolder so this test is deterministic regardless of CWD
        var allowedFolder = Path.Combine(Path.GetTempPath(), "unique-allowed-" + Guid.NewGuid().ToString("N")[..8]);
        var fileSystemConnectorMock = new Mock<IFileSystemConnector>();
        var documentConnectorMock = new Mock<IDocumentConnector>();
        var target = new DocumentPlugin(documentConnectorMock.Object, fileSystemConnectorMock.Object)
        {
            AllowedDirectories = [allowedFolder]
        };

        // Act & Assert — relative paths resolve to CWD after canonicalization,
        // which will be outside the allowed directories
        await Assert.ThrowsAsync<InvalidOperationException>(async () => await target.ReadTextAsync("myfile.docx"));
        await Assert.ThrowsAsync<InvalidOperationException>(async () => await target.AppendTextAsync("text", "myfile.docx"));
    }

    [Fact]
    public async Task ItDeniesEnvVarExpansionBypassOnReadAsync()
    {
        // Arrange — use a test-specific env var that expands to a value containing
        // a path separator + ".." which creates a traversal after expansion.
        var allowedFolder = Path.Combine(Path.GetTempPath(), "allowed-sandbox");
        var envVarName = "SK_TEST_EXPAND_" + Guid.NewGuid().ToString("N")[..8];

        try
        {
            // The env var value starts with a separator + ".." so that after expansion
            // the path becomes: allowed-sandbox/<sep>..<sep>elsewhere<sep>secret.docx
            Environment.SetEnvironmentVariable(envVarName,
                $"{Path.DirectorySeparatorChar}..{Path.DirectorySeparatorChar}elsewhere");
            var maliciousPath = Path.Combine(allowedFolder, $"%{envVarName}%", "secret.docx");

            var fileSystemConnectorMock = new Mock<IFileSystemConnector>();
            var documentConnectorMock = new Mock<IDocumentConnector>();
            var target = new DocumentPlugin(documentConnectorMock.Object, fileSystemConnectorMock.Object)
            {
                AllowedDirectories = [allowedFolder]
            };

            // Act & Assert — the path should be denied because env vars are expanded
            // before validation, so the canonical path lands outside the allowed directory.
            await Assert.ThrowsAsync<InvalidOperationException>(async () => await target.ReadTextAsync(maliciousPath));
        }
        finally
        {
            Environment.SetEnvironmentVariable(envVarName, null);
        }
    }

    [Fact]
    public async Task ItDeniesEnvVarExpansionBypassOnWriteAsync()
    {
        // Arrange — same pattern as read test, for the write path.
        var allowedFolder = Path.Combine(Path.GetTempPath(), "allowed-sandbox");
        var envVarName = "SK_TEST_EXPAND_W_" + Guid.NewGuid().ToString("N")[..8];

        try
        {
            Environment.SetEnvironmentVariable(envVarName,
                $"{Path.DirectorySeparatorChar}..{Path.DirectorySeparatorChar}elsewhere");
            var maliciousPath = Path.Combine(allowedFolder, $"%{envVarName}%", "secret.docx");

            var fileSystemConnectorMock = new Mock<IFileSystemConnector>();
            var documentConnectorMock = new Mock<IDocumentConnector>();
            var target = new DocumentPlugin(documentConnectorMock.Object, fileSystemConnectorMock.Object)
            {
                AllowedDirectories = [allowedFolder]
            };

            // Act & Assert
            await Assert.ThrowsAsync<InvalidOperationException>(async () => await target.AppendTextAsync("text", maliciousPath));
        }
        finally
        {
            Environment.SetEnvironmentVariable(envVarName, null);
        }
    }

    [Fact]
    public async Task ItDeniesEnvVarExpansionToAbsolutePathAsync()
    {
        // Arrange — env var that expands to an absolute path outside the sandbox
        var allowedFolder = Path.Combine(Path.GetTempPath(), "sandbox");
        var envVarName = "SK_TEST_ABS_" + Guid.NewGuid().ToString("N")[..8];
        var outsidePath = Path.Combine(Path.GetTempPath(), "outside");

        try
        {
            Environment.SetEnvironmentVariable(envVarName, outsidePath);
            var maliciousPath = Path.Combine($"%{envVarName}%", "secret.docx");

            var fileSystemConnectorMock = new Mock<IFileSystemConnector>();
            var documentConnectorMock = new Mock<IDocumentConnector>();
            var target = new DocumentPlugin(documentConnectorMock.Object, fileSystemConnectorMock.Object)
            {
                AllowedDirectories = [allowedFolder]
            };

            // Act & Assert — after env-var expansion, the path resolves outside the sandbox
            await Assert.ThrowsAsync<InvalidOperationException>(async () => await target.ReadTextAsync(maliciousPath));
        }
        finally
        {
            Environment.SetEnvironmentVariable(envVarName, null);
        }
    }

    [Fact]
    public async Task ItDeniesUncPathsIntroducedViaEnvVarExpansionAsync()
    {
        // Arrange — env var that expands to a UNC path
        var allowedFolder = Path.Combine(Path.GetTempPath(), "sandbox");
        var envVarName = "SK_TEST_UNC_" + Guid.NewGuid().ToString("N")[..8];

        try
        {
            Environment.SetEnvironmentVariable(envVarName, @"\\evil-server\share");
            var maliciousPath = $"%{envVarName}%{Path.DirectorySeparatorChar}secret.docx";

            var fileSystemConnectorMock = new Mock<IFileSystemConnector>();
            var documentConnectorMock = new Mock<IDocumentConnector>();
            var target = new DocumentPlugin(documentConnectorMock.Object, fileSystemConnectorMock.Object)
            {
                AllowedDirectories = [allowedFolder]
            };

            // Act & Assert — expanded path is UNC, should be rejected
            await Assert.ThrowsAsync<ArgumentException>(async () => await target.ReadTextAsync(maliciousPath));
        }
        finally
        {
            Environment.SetEnvironmentVariable(envVarName, null);
        }
    }
}
