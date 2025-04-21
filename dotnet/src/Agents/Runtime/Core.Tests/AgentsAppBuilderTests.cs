// Copyright (c) Microsoft. All rights reserved.

using System.Reflection;
using System.Threading.Tasks;
using FluentAssertions;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Runtime.InProcess;
using Xunit;

namespace Microsoft.SemanticKernel.Agents.Runtime.Core.Tests;

[Trait("Category", "Unit")]
public class AgentsAppBuilderTests
{
    [Fact]
    public void Constructor_WithoutParameters_ShouldCreateNewHostApplicationBuilder()
    {
        // Act
        AgentsAppBuilder builder = new();

        // Assert
        builder.Services.Should().NotBeNull();
        builder.Configuration.Should().NotBeNull();
    }

    [Fact]
    public void Constructor_WithBaseBuilder_ShouldUseProvidedBuilder()
    {
        // Arrange
        HostApplicationBuilder baseBuilder = new();

        // Add a test service to verify it's the same builder
        baseBuilder.Services.AddSingleton<ITestService, TestService>();

        // Act
        AgentsAppBuilder builder = new(baseBuilder);

        // Assert
        builder.Services.Should().BeSameAs(baseBuilder.Services);
        builder.Services.BuildServiceProvider().GetService<ITestService>().Should().NotBeNull();
    }

    [Fact]
    public void Services_ShouldReturnBuilderServices()
    {
        // Arrange
        AgentsAppBuilder builder = new();

        // Act
        IServiceCollection services = builder.Services;

        // Assert
        services.Should().NotBeNull();
    }

    [Fact]
    public void Configuration_ShouldReturnBuilderConfiguration()
    {
        // Arrange
        AgentsAppBuilder builder = new();

        // Act
        IConfiguration configuration = builder.Configuration;

        // Assert
        configuration.Should().NotBeNull();
    }

    [Fact]
    public async Task UseRuntime_ShouldRegisterRuntimeInServices()
    {
        // Arrange
        AgentsAppBuilder builder = new();
        await using InProcessRuntime runtime = new();

        // Act
        AgentsAppBuilder result = builder.UseRuntime(runtime);

        // Assert
        result.Should().BeSameAs(builder);
        IAgentRuntime? resolvedRuntime = builder.Services.BuildServiceProvider().GetService<IAgentRuntime>();
        resolvedRuntime.Should().BeSameAs(runtime);

        // Verify it's also registered as a hosted service
        IHostedService? hostedService = builder.Services.BuildServiceProvider().GetService<IHostedService>();
        hostedService.Should().BeSameAs(runtime);
    }

    [Fact]
    public void AddAgentsFromAssemblies_WithoutParameters_ShouldScanCurrentDomain()
    {
        // Arrange
        AgentsAppBuilder builder = new();

        // Act - using the parameterless version calls AppDomain.CurrentDomain.GetAssemblies()
        builder.AddAgentsFromAssemblies();

        // Assert
        // We just verify it doesn't throw, as the actual agents registered depend on the loaded assemblies
    }

    [Fact]
    public void AddAgentsFromAssemblies_WithAssemblies_ShouldRegisterAgentsFromProvidedAssemblies()
    {
        // Arrange
        AgentsAppBuilder builder = new();
        Assembly testAssembly = typeof(TestAgent).Assembly;

        // Act
        AgentsAppBuilder result = builder.AddAgentsFromAssemblies(testAssembly);

        // Assert
        result.Should().BeSameAs(builder);
        // The assertion on actual agent registration is done in BuildAsync test
    }

    [Fact]
    public void AddAgent_ShouldRegisterAgentType()
    {
        // Arrange
        AgentsAppBuilder builder = new();
        AgentType agentType = new("TestAgent");

        // Act
        AgentsAppBuilder result = builder.AddAgent<TestAgent>(agentType);

        // Assert
        result.Should().BeSameAs(builder);
        // Actual agent registration is tested in BuildAsync
    }

    [Fact]
    public async Task BuildAsync_ShouldReturnAgentsAppWithRegisteredAgents()
    {
        // Arrange
        AgentsAppBuilder builder = new();
        await using InProcessRuntime runtime = new();
        builder.UseRuntime(runtime);

        AgentType testAgentType = new("TestAgent");
        builder.AddAgent<TestAgent>(testAgentType);

        // Act
        AgentsApp app = await builder.BuildAsync();
        AgentId agentId = await runtime.GetAgentAsync(testAgentType);

        // Assert
        app.Should().NotBeNull();
        app.Host.Should().NotBeNull();
        app.AgentRuntime.Should().BeSameAs(runtime);
        agentId.Type.Should().BeSameAs(testAgentType.Name);
    }

    // Private test interfaces and classes to support the tests
    private interface ITestService { }

    private sealed class TestService : ITestService { }

    private sealed class TestAgent : BaseAgent
    {
        public TestAgent(AgentId id, IAgentRuntime runtime, string description, ILogger<BaseAgent>? logger = null)
            : base(id, runtime, description, logger) { }
    }
}
