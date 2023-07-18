// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Skills.MsGraph;
using Moq;
using Xunit;

namespace SemanticKernel.Skills.UnitTests.MsGraph;

public class CloudDriveSkillTests
{
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
}
