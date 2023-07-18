// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Skills.MsGraph;
using Moq;
using SemanticKernel.Skills.UnitTests.XunitHelpers;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.Skills.UnitTests.MsGraph;

public class CloudDriveSkillTests : IDisposable
{
    private readonly XunitLogger<SKContext> _logger;
    private readonly SKContext _context;
    private bool _disposedValue = false;

    public CloudDriveSkillTests(ITestOutputHelper output)
    {
        this._logger = new XunitLogger<SKContext>(output);
        this._context = new SKContext(new ContextVariables(), null, this._logger, CancellationToken.None);
    }

    [Fact]
    public async Task UploadSmallFileAsyncSucceedsAsync()
    {
        // Arrange
        string anyFilePath = Guid.NewGuid().ToString();

        Mock<ICloudDriveConnector> connectorMock = new();
        connectorMock.Setup(c => c.UploadSmallFileAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask);

        CloudDriveSkill target = new(connectorMock.Object);

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

        CloudDriveSkill target = new(connectorMock.Object);

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

        CloudDriveSkill target = new(connectorMock.Object);

        // Act
        string actual = await target.GetFileContentAsync(anyFilePath);

        // Assert
        Assert.Equal(expectedContent, actual);
        connectorMock.VerifyAll();
    }

    protected virtual void Dispose(bool disposing)
    {
        if (!this._disposedValue)
        {
            if (disposing)
            {
                this._logger.Dispose();
            }

            this._disposedValue = true;
        }
    }

    public void Dispose()
    {
        // Do not change this code. Put cleanup code in 'Dispose(bool disposing)' method
        this.Dispose(disposing: true);
        GC.SuppressFinalize(this);
    }
}
