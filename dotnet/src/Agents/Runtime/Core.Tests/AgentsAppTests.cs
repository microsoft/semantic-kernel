// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using FluentAssertions;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Moq;
using Xunit;

namespace Microsoft.SemanticKernel.Agents.Runtime.Core.Tests;

[Trait("Category", "Unit")]
public class AgentsAppTests
{
    [Fact]
    public void Constructor_ShouldInitializeHost()
    {
        // Arrange
        Mock<IHost> mockHost = new();

        // Act
        AgentsApp agentsApp = new(mockHost.Object);

        // Assert
        agentsApp.Host.Should().BeSameAs(mockHost.Object);
    }

    [Fact]
    public void Services_ShouldReturnHostServices()
    {
        // Arrange
        Mock<IServiceProvider> mockServiceProvider = new();
        Mock<IHost> mockHost = new();
        mockHost.Setup(h => h.Services).Returns(mockServiceProvider.Object);
        AgentsApp agentsApp = new(mockHost.Object);

        // Act
        IServiceProvider result = agentsApp.Services;

        // Assert
        result.Should().BeSameAs(mockServiceProvider.Object);
    }

    [Fact]
    public void ApplicationLifetime_ShouldGetFromServices()
    {
        // Arrange
        Mock<IHostApplicationLifetime> mockLifetime = new();
        ServiceProvider serviceProvider = new ServiceCollection()
            .AddSingleton(mockLifetime.Object)
            .BuildServiceProvider();

        Mock<IHost> mockHost = new();
        mockHost.Setup(h => h.Services).Returns(serviceProvider);

        AgentsApp agentsApp = new(mockHost.Object);

        // Act
        IHostApplicationLifetime result = agentsApp.ApplicationLifetime;

        // Assert
        result.Should().BeSameAs(mockLifetime.Object);
    }

    [Fact]
    public void AgentRuntime_ShouldGetFromServices()
    {
        // Arrange
        Mock<IAgentRuntime> mockAgentRuntime = new();
        ServiceProvider serviceProvider = new ServiceCollection()
            .AddSingleton(mockAgentRuntime.Object)
            .BuildServiceProvider();

        Mock<IHost> mockHost = new();
        mockHost.Setup(h => h.Services).Returns(serviceProvider);

        AgentsApp agentsApp = new(mockHost.Object);

        // Act
        IAgentRuntime result = agentsApp.AgentRuntime;

        // Assert
        result.Should().BeSameAs(mockAgentRuntime.Object);
    }

    [Fact]
    public async Task StartAsync_ShouldStartHost()
    {
        // Arrange
        Mock<IHost> mockHost = new();
        mockHost.Setup(h => h.StartAsync(It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask);

        AgentsApp agentsApp = new(mockHost.Object);

        // Act
        await agentsApp.StartAsync();

        // Assert
        mockHost.Verify(h => h.StartAsync(It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task StartAsync_WhenAlreadyRunning_ShouldThrowInvalidOperationException()
    {
        // Arrange
        Mock<IHost> mockHost = new();
        AgentsApp agentsApp = new(mockHost.Object);

        // Act & Assert
        await agentsApp.StartAsync();
        await Assert.ThrowsAsync<InvalidOperationException>(() => agentsApp.StartAsync().AsTask());
    }

    [Fact]
    public async Task ShutdownAsync_ShouldStopHost()
    {
        // Arrange
        Mock<IHost> mockHost = new();
        mockHost.Setup(h => h.StopAsync(It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask);

        AgentsApp agentsApp = new(mockHost.Object);
        await agentsApp.StartAsync(); // Start first so we can shut down

        // Act
        await agentsApp.ShutdownAsync();

        // Assert
        mockHost.Verify(h => h.StopAsync(It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task ShutdownAsync_WhenNotRunning_ShouldThrowInvalidOperationException()
    {
        // Arrange
        Mock<IHost> mockHost = new();
        AgentsApp agentsApp = new(mockHost.Object);

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(() => agentsApp.ShutdownAsync().AsTask());
    }

    [Fact]
    public async Task PublishMessageAsync_WhenNotRunning_ShouldStartHostFirst()
    {
        // Arrange
        Mock<IAgentRuntime> mockAgentRuntime = new();
        ServiceProvider serviceProvider = new ServiceCollection()
            .AddSingleton(mockAgentRuntime.Object)
            .BuildServiceProvider();

        Mock<IHost> mockHost = new();
        mockHost.Setup(h => h.Services).Returns(serviceProvider);
        mockHost.Setup(h => h.StartAsync(It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask);

        AgentsApp agentsApp = new(mockHost.Object);

        string message = "test message";
        TopicId topic = new("test-topic");

        // Act
        await agentsApp.PublishMessageAsync(message, topic);

        // Assert
        mockHost.Verify(h => h.StartAsync(It.IsAny<CancellationToken>()), Times.Once);
        mockAgentRuntime.Verify(
            r =>
            r.PublishMessageAsync(
                message,
                topic,
                It.IsAny<AgentId?>(),
                It.IsAny<string>(),
                It.IsAny<CancellationToken>()),
                Times.Once);
    }

    [Fact]
    public async Task PublishMessageAsync_WhenRunning_ShouldNotStartHostAgain()
    {
        // Arrange
        Mock<IAgentRuntime> mockAgentRuntime = new();
        ServiceProvider serviceProvider = new ServiceCollection()
            .AddSingleton(mockAgentRuntime.Object)
            .BuildServiceProvider();

        Mock<IHost> mockHost = new();
        mockHost.Setup(h => h.Services).Returns(serviceProvider);
        mockHost.Setup(h => h.StartAsync(It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask);

        AgentsApp agentsApp = new(mockHost.Object);
        await agentsApp.StartAsync(); // Start first

        string message = "test message";
        TopicId topic = new("test-topic");

        // Act
        await agentsApp.PublishMessageAsync(message, topic);

        // Assert
        mockHost.Verify(h => h.StartAsync(It.IsAny<CancellationToken>()), Times.Once);
        mockAgentRuntime.Verify(
            r =>
                r.PublishMessageAsync(
                    message,
                    topic,
                    It.IsAny<AgentId?>(),
                    It.IsAny<string>(),
                    It.IsAny<CancellationToken>()),
                    Times.Once);
    }

    [Fact]
    public async Task PublishMessageAsync_ShouldPassAllParameters()
    {
        // Arrange
        Mock<IAgentRuntime> mockAgentRuntime = new();
        ServiceProvider serviceProvider = new ServiceCollection()
            .AddSingleton(mockAgentRuntime.Object)
            .BuildServiceProvider();

        Mock<IHost> mockHost = new();
        mockHost.Setup(h => h.Services).Returns(serviceProvider);

        AgentsApp agentsApp = new(mockHost.Object);
        await agentsApp.StartAsync();

        string message = "test message";
        TopicId topic = new("test-topic");
        string messageId = "test-message-id";

        // Act
        await agentsApp.PublishMessageAsync(message, topic, messageId, CancellationToken.None);

        // Assert
        mockAgentRuntime.Verify(
            r =>
                r.PublishMessageAsync(
                    message,
                    topic,
                    It.IsAny<AgentId?>(),
                    messageId,
                    CancellationToken.None),
                    Times.Once);
    }

    [Fact]
    public async Task WaitForShutdownAsync_ShouldBlock()
    {
        // Arrange
        IHost host = new HostApplicationBuilder().Build();

        AgentsApp agentsApp = new(host);
        await agentsApp.StartAsync();

        ValueTask shutdownTask = ValueTask.CompletedTask;
        try
        {
            // Assert - Verify initial state
            agentsApp.ApplicationLifetime.ApplicationStopped.IsCancellationRequested.Should().BeFalse();

            // Act
            shutdownTask = agentsApp.ShutdownAsync();
            await agentsApp.WaitForShutdownAsync();

            // Assert
            agentsApp.ApplicationLifetime.ApplicationStopped.IsCancellationRequested.Should().BeTrue();
        }
        finally
        {
            await shutdownTask; // Ensure shutdown completes
        }
    }
}
