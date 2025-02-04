// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.AI.CrewAI;
using Moq;
using Xunit;

namespace SemanticKernel.Plugins.UnitTests.AI.CrewAI;

/// <summary>
/// Unit tests for the <see cref="CrewAIEnterprise"/> class.
/// </summary>
public sealed class CrewAIEnterpriseTests
{
    private readonly Mock<ICrewAIEnterpriseClient> _mockClient;
    private readonly CrewAIEnterprise _crewAIEnterprise;

    /// <summary>
    /// Initializes a new instance of the <see cref="CrewAIEnterpriseTests"/> class.
    /// </summary>
    public CrewAIEnterpriseTests()
    {
        this._mockClient = new Mock<ICrewAIEnterpriseClient>(MockBehavior.Strict);
        this._crewAIEnterprise = new CrewAIEnterprise(this._mockClient.Object, NullLoggerFactory.Instance);
    }

    /// <summary>
    /// Tests the successful kickoff of a CrewAI task.
    /// </summary>
    [Fact]
    public async Task KickoffAsyncSuccessAsync()
    {
        // Arrange
        var response = new CrewAIKickoffResponse { KickoffId = "12345" };
        this._mockClient.Setup(client => client.KickoffAsync(It.IsAny<object>(), null, null, null, It.IsAny<CancellationToken>()))
                        .ReturnsAsync(response);

        // Act
        var result = await this._crewAIEnterprise.KickoffAsync(new { });

        // Assert
        Assert.Equal("12345", result);
    }

    /// <summary>
    /// Tests the failure of a CrewAI task kickoff.
    /// </summary>
    [Fact]
    public async Task KickoffAsyncFailureAsync()
    {
        // Arrange
        this._mockClient.Setup(client => client.KickoffAsync(It.IsAny<object>(), null, null, null, It.IsAny<CancellationToken>()))
                        .ThrowsAsync(new InvalidOperationException("Kickoff failed"));

        // Act & Assert
        await Assert.ThrowsAsync<KernelException>(() => this._crewAIEnterprise.KickoffAsync(new { }));
    }

    /// <summary>
    /// Tests the successful retrieval of CrewAI task status.
    /// </summary>
    [Fact]
    public async Task GetCrewStatusAsyncSuccessAsync()
    {
        // Arrange
        var response = new CrewAIStatusResponse { State = CrewAIKickoffState.Running };
        this._mockClient.Setup(client => client.GetStatusAsync("12345", It.IsAny<CancellationToken>()))
                        .ReturnsAsync(response);

        // Act
        var result = await this._crewAIEnterprise.GetCrewKickoffStatusAsync("12345");

        // Assert
        Assert.Equal(CrewAIKickoffState.Running, result.State);
    }

    /// <summary>
    /// Tests the failure of CrewAI task status retrieval.
    /// </summary>
    [Fact]
    public async Task GetCrewStatusAsyncFailureAsync()
    {
        // Arrange
        this._mockClient.Setup(client => client.GetStatusAsync("12345", It.IsAny<CancellationToken>()))
                        .ThrowsAsync(new InvalidOperationException("Status retrieval failed"));

        // Act & Assert
        await Assert.ThrowsAsync<KernelException>(() => this._crewAIEnterprise.GetCrewKickoffStatusAsync("12345"));
    }

    /// <summary>
    /// Tests the successful completion of a CrewAI task.
    /// </summary>
    [Fact]
    public async Task WaitForCrewCompletionAsyncSuccessAsync()
    {
        // Arrange
        var response = new CrewAIStatusResponse { State = CrewAIKickoffState.Success, Result = "Completed" };
        this._mockClient.SetupSequence(client => client.GetStatusAsync("12345", It.IsAny<CancellationToken>()))
                        .ReturnsAsync(new CrewAIStatusResponse { State = CrewAIKickoffState.Running })
                        .ReturnsAsync(response);

        // Act
        var result = await this._crewAIEnterprise.WaitForCrewCompletionAsync("12345");

        // Assert
        Assert.Equal("Completed", result);
    }

    /// <summary>
    /// Tests the failure of a CrewAI task completion.
    /// </summary>
    [Fact]
    public async Task WaitForCrewCompletionAsyncFailureAsync()
    {
        // Arrange
        var response = new CrewAIStatusResponse { State = CrewAIKickoffState.Failed, Result = "Error" };
        this._mockClient.SetupSequence(client => client.GetStatusAsync("12345", It.IsAny<CancellationToken>()))
                        .ReturnsAsync(new CrewAIStatusResponse { State = CrewAIKickoffState.Running })
                        .ReturnsAsync(response);

        // Act & Assert
        var exception = await Assert.ThrowsAsync<KernelException>(() => this._crewAIEnterprise.WaitForCrewCompletionAsync("12345"));
    }

    /// <summary>
    /// Tests the successful creation of a Kernel plugin.
    /// </summary>
    [Fact]
    public void CreateKernelPluginSuccess()
    {
        // Arrange
        var inputDefinitions = new List<CrewAIInputMetadata>
        {
            new("input1", "description1", typeof(string))
        };

        // Act
        var plugin = this._crewAIEnterprise.CreateKernelPlugin("TestPlugin", "Test Description", inputDefinitions);

        // Assert
        Assert.NotNull(plugin);
        Assert.Equal("TestPlugin", plugin.Name);
    }
}
