// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Skills.Document;
using Microsoft.SemanticKernel.Skills.Document.FileSystem;
using Moq;
using Xunit;

namespace SemanticKernel.Skills.UnitTests.Document;

public class DocumentSkillTests
{
    private readonly SKContext _context = new(new ContextVariables(), null, NullLogger.Instance);

    [Fact]
    public async Task ReadTextAsyncSucceedsAsync()
    {
        // Arrange
        var expectedText = Guid.NewGuid().ToString();
        var anyFilePath = Guid.NewGuid().ToString();

        var fileSystemConnectorMock = new Mock<IFileSystemConnector>();
        fileSystemConnectorMock
            .Setup(mock => mock.GetFileContentStreamAsync(It.Is<string>(filePath => filePath.Equals(anyFilePath, StringComparison.Ordinal)),
                It.IsAny<CancellationToken>()))
            .ReturnsAsync(Stream.Null);

        var documentConnectorMock = new Mock<IDocumentConnector>();
        documentConnectorMock
            .Setup(mock => mock.ReadText(It.IsAny<Stream>()))
            .Returns(expectedText);

        var target = new DocumentSkill(documentConnectorMock.Object, fileSystemConnectorMock.Object);

        // Act
        string actual = await target.ReadTextAsync(anyFilePath);

        // Assert
        Assert.Equal(expectedText, actual);
        Assert.False(this._context.ErrorOccurred);
        fileSystemConnectorMock.VerifyAll();
        documentConnectorMock.VerifyAll();
    }

    [Fact]
    public async Task AppendTextAsyncFileExistsSucceedsAsync()
    {
        // Arrange
        var anyText = Guid.NewGuid().ToString();
        var anyFilePath = Guid.NewGuid().ToString();

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

        var target = new DocumentSkill(documentConnectorMock.Object, fileSystemConnectorMock.Object);

        // Act
        await target.AppendTextAsync(anyText, anyFilePath);

        // Assert
        Assert.False(this._context.ErrorOccurred);
        fileSystemConnectorMock.VerifyAll();
        documentConnectorMock.VerifyAll();
    }

    [Fact]
    public async Task AppendTextAsyncFileDoesNotExistSucceedsAsync()
    {
        // Arrange
        var anyText = Guid.NewGuid().ToString();
        var anyFilePath = Guid.NewGuid().ToString();

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

        var target = new DocumentSkill(documentConnectorMock.Object, fileSystemConnectorMock.Object);

        // Act
        await target.AppendTextAsync(anyText, anyFilePath);

        // Assert
        Assert.False(this._context.ErrorOccurred);
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

        var target = new DocumentSkill(documentConnectorMock.Object, fileSystemConnectorMock.Object);

        // Act/Assert
        await Assert.ThrowsAnyAsync<ArgumentException>(() =>
           target.AppendTextAsync(anyText, null!));

        // Assert
        fileSystemConnectorMock.Verify(mock => mock.GetWriteableFileStreamAsync(It.IsAny<string>(), It.IsAny<CancellationToken>()), Times.Never());
        documentConnectorMock.Verify(mock => mock.AppendText(It.IsAny<Stream>(), It.IsAny<string>()), Times.Never());
    }
}
