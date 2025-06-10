// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Agents.CopilotStudio.Client.Discovery;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Agents.Copilot;
using Moq;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.CopilotStudio;

/// <summary>
/// Unit tests for the <see cref="CopilotStudioConnectionSettings"/> class.
/// </summary>
public class CopilotStudioConnectionSettingsTests
{
    /// <summary>
    /// Verifies that the constructor with all parameters sets properties correctly.
    /// </summary>
    [Fact]
    public void Constructor_WithAllParameters_SetsPropertiesCorrectly()
    {
        // Arrange
        string tenantId = "testTenantId";
        string appClientId = "testAppClientId";
        string appClientSecret = "testAppClientSecret";

        // Act
        CopilotStudioConnectionSettings settings = new(tenantId, appClientId, appClientSecret);

        // Assert
        Assert.Equal(tenantId, settings.TenantId);
        Assert.Equal(appClientId, settings.AppClientId);
        Assert.Equal(appClientSecret, settings.AppClientSecret);
        Assert.Equal(PowerPlatformCloud.Prod, settings.Cloud);
        Assert.Equal(AgentType.Published, settings.CopilotAgentType);
        Assert.True(settings.UseInteractiveAuthentication);
    }

    /// <summary>
    /// Verifies that the constructor with required parameters sets properties correctly.
    /// </summary>
    [Fact]
    public void Constructor_WithRequiredParameters_SetsPropertiesCorrectly()
    {
        // Arrange
        string tenantId = "testTenantId";
        string appClientId = "testAppClientId";

        // Act
        CopilotStudioConnectionSettings settings = new(tenantId, appClientId);

        // Assert
        Assert.Equal(tenantId, settings.TenantId);
        Assert.Equal(appClientId, settings.AppClientId);
        Assert.Null(settings.AppClientSecret);
        Assert.Equal(PowerPlatformCloud.Prod, settings.Cloud);
        Assert.Equal(AgentType.Published, settings.CopilotAgentType);
        Assert.True(settings.UseInteractiveAuthentication);
    }

    /// <summary>
    /// Verifies that the constructor with configuration sets properties correctly.
    /// </summary>
    [Fact]
    public void Constructor_WithConfiguration_SetsPropertiesCorrectly()
    {
        // Arrange
        string tenantId = "testTenantId";
        string appClientId = "testAppClientId";
        string appClientSecret = "testAppClientSecret";

        Mock<IConfigurationSection> mockConfig = new();
        mockConfig.Setup(c => c[nameof(CopilotStudioConnectionSettings.TenantId)]).Returns(tenantId);
        mockConfig.Setup(c => c[nameof(CopilotStudioConnectionSettings.AppClientId)]).Returns(appClientId);
        mockConfig.Setup(c => c[nameof(CopilotStudioConnectionSettings.AppClientSecret)]).Returns(appClientSecret);

        // Act
        CopilotStudioConnectionSettings settings = new(mockConfig.Object);

        // Assert
        Assert.Equal(tenantId, settings.TenantId);
        Assert.Equal(appClientId, settings.AppClientId);
        Assert.Equal(appClientSecret, settings.AppClientSecret);
        Assert.True(settings.UseInteractiveAuthentication);
    }

    /// <summary>
    /// Verifies that the constructor throws an exception when AppClientId is missing in configuration.
    /// </summary>
    [Fact]
    public void Constructor_WithConfigurationMissingAppClientId_ThrowsArgumentException()
    {
        // Arrange
        string tenantId = "testTenantId";

        Mock<IConfigurationSection> mockConfig = new();
        mockConfig.Setup(c => c[nameof(CopilotStudioConnectionSettings.TenantId)]).Returns(tenantId);
        mockConfig.Setup(c => c[nameof(CopilotStudioConnectionSettings.AppClientId)]).Returns((string)null!);

        // Act & Assert
        ArgumentException exception = Assert.Throws<ArgumentException>(() =>
            new CopilotStudioConnectionSettings(mockConfig.Object));
        Assert.Contains("AppClientId", exception.Message);
    }

    /// <summary>
    /// Verifies that the constructor throws an exception when TenantId is missing in configuration.
    /// </summary>
    [Fact]
    public void Constructor_WithConfigurationMissingTenantId_ThrowsArgumentException()
    {
        // Arrange
        string appClientId = "testAppClientId";

        Mock<IConfigurationSection> mockConfig = new();
        mockConfig.Setup(c => c[nameof(CopilotStudioConnectionSettings.TenantId)]).Returns((string)null!);
        mockConfig.Setup(c => c[nameof(CopilotStudioConnectionSettings.AppClientId)]).Returns(appClientId);

        // Act & Assert
        ArgumentException exception = Assert.Throws<ArgumentException>(() =>
            new CopilotStudioConnectionSettings(mockConfig.Object));
        Assert.Contains("TenantId", exception.Message);
    }

    /// <summary>
    /// Verifies that the constructor does not throw when AppClientSecret is missing in configuration.
    /// </summary>
    [Fact]
    public void Constructor_WithConfigurationMissingAppClientSecret_DoesNotThrow()
    {
        // Arrange
        string tenantId = "testTenantId";
        string appClientId = "testAppClientId";

        Mock<IConfigurationSection> mockConfig = new();
        mockConfig.Setup(c => c[nameof(CopilotStudioConnectionSettings.TenantId)]).Returns(tenantId);
        mockConfig.Setup(c => c[nameof(CopilotStudioConnectionSettings.AppClientId)]).Returns(appClientId);
        mockConfig.Setup(c => c[nameof(CopilotStudioConnectionSettings.AppClientSecret)]).Returns((string)null!);

        // Act & Assert - Should not throw
        CopilotStudioConnectionSettings settings = new(mockConfig.Object);

        // Additional verification
        Assert.Equal(tenantId, settings.TenantId);
        Assert.Equal(appClientId, settings.AppClientId);
        Assert.Null(settings.AppClientSecret);
    }

    /// <summary>
    /// Verifies that the default value of UseInteractiveAuthentication is true.
    /// </summary>
    [Fact]
    public void UseInteractiveAuthentication_DefaultValue_IsTrue()
    {
        // Arrange & Act
        CopilotStudioConnectionSettings settings = new("testTenantId", "testAppClientId");

        // Assert
        Assert.True(settings.UseInteractiveAuthentication);
    }

    /// <summary>
    /// Verifies that UseInteractiveAuthentication property can be modified.
    /// </summary>
    [Fact]
    public void UseInteractiveAuthentication_CanBeModified()
    {
        // Arrange
        CopilotStudioConnectionSettings settings = new("testTenantId", "testAppClientId")
        {
            UseInteractiveAuthentication = false
        };

        // Assert
        Assert.False(settings.UseInteractiveAuthentication);
    }

    /// <summary>
    /// Verifies that the default value of Cloud property is Prod.
    /// </summary>
    [Fact]
    public void DefaultCloud_IsProd()
    {
        // Arrange & Act
        CopilotStudioConnectionSettings settings = new("testTenantId", "testAppClientId");

        // Assert
        Assert.Equal(PowerPlatformCloud.Prod, settings.Cloud);
    }

    /// <summary>
    /// Verifies that the default value of CopilotAgentType property is Published.
    /// </summary>
    [Fact]
    public void DefaultCopilotAgentType_IsPublished()
    {
        // Arrange & Act
        CopilotStudioConnectionSettings settings = new("testTenantId", "testAppClientId");

        // Assert
        Assert.Equal(AgentType.Published, settings.CopilotAgentType);
    }
}
