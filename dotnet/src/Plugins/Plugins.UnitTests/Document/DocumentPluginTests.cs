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
        // Arrange
        var fileSystemConnectorMock = new Mock<IFileSystemConnector>();
        var documentConnectorMock = new Mock<IDocumentConnector>();
        var target = new DocumentPlugin(documentConnectorMock.Object, fileSystemConnectorMock.Object)
        {
            AllowedDirectories = [Path.GetTempPath()]
        };

        // Act & Assert — relative paths are caught by the "fully qualified" check
        await Assert.ThrowsAsync<ArgumentException>(async () => await target.ReadTextAsync("myfile.docx"));
    }
}
