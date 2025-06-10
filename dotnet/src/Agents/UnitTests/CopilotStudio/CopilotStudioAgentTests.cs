// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Agents.CopilotStudio.Client;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Agents.Copilot;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.CopilotStudio;

public class CopilotStudioAgentTests
{
    [Fact]
    public void CreateClient_WithValidSettings_ReturnsConfiguredClient()
    {
        // Arrange
        CopilotStudioConnectionSettings settings = new("test-tenant-id", "test-app-client-id", "test-app-client-secret");
        ILogger logger = NullLogger.Instance;

        // Act
        CopilotClient client = CopilotStudioAgent.CreateClient(settings, logger);

        // Assert
        Assert.NotNull(client);
        Assert.IsType<CopilotClient>(client);
    }

    [Fact]
    public void CreateClient_WithNullLogger_UsesNullLogger()
    {
        // Arrange
        CopilotStudioConnectionSettings settings = new("test-tenant-id", "test-app-client-id", "test-app-client-secret");

        // Act
        CopilotClient client = CopilotStudioAgent.CreateClient(settings);

        // Assert
        Assert.NotNull(client);
        Assert.IsType<CopilotClient>(client);
    }
}
