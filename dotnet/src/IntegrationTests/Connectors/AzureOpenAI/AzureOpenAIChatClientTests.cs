// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text;
using System.Threading.Tasks;
using Azure.Identity;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.AzureOpenAI;

public sealed class AzureOpenAIChatClientTests : BaseIntegrationTest
{
    [Fact]
    public async Task ItCanUseAzureOpenAIChatClientAsync()
    {
        // Arrange
        Assert.NotNull(this._configuration.ChatDeploymentName);
        Assert.NotNull(this._configuration.Endpoint);

        // Create a kernel with the AzureOpenAI chat client
        var builder = Kernel.CreateBuilder();
        builder.Services.AddAzureOpenAIChatClient(
            this._configuration.ChatDeploymentName,
            this._configuration.Endpoint,
            new AzureCliCredential());
        var kernel = builder.Build();

        // Act
        var chatClient = kernel.GetRequiredService<IChatClient>();
        var response = await chatClient.GetResponseAsync("List the planets in the solar system");

        // Assert
        Assert.NotNull(response);
        Assert.NotEmpty(response.Text);
        Assert.Contains("Mercury", response.Text, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("Venus", response.Text, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("Earth", response.Text, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("Mars", response.Text, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("Jupiter", response.Text, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("Saturn", response.Text, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("Uranus", response.Text, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("Neptune", response.Text, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task ItCanUseAzureOpenAIChatClientStreamingAsync()
    {
        // Arrange
        Assert.NotNull(this._configuration.ChatDeploymentName);
        Assert.NotNull(this._configuration.Endpoint);

        // Create a kernel with the AzureOpenAI chat client
        var builder = Kernel.CreateBuilder();
        builder.Services.AddAzureOpenAIChatClient(
            this._configuration.ChatDeploymentName,
            this._configuration.Endpoint,
            new AzureCliCredential());
        var kernel = builder.Build();

        // Act
        var chatClient = kernel.GetRequiredService<IChatClient>();
        var stringBuilder = new StringBuilder();
        await foreach (var update in chatClient.GetStreamingResponseAsync("List the planets in the solar system"))
        {
            stringBuilder.Append(update.Text);
        }
        var response = stringBuilder.ToString();

        // Assert
        Assert.NotNull(response);
        Assert.NotEmpty(response);
        Assert.Contains("Mercury", response, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("Venus", response, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("Earth", response, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("Mars", response, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("Jupiter", response, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("Saturn", response, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("Uranus", response, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("Neptune", response, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task ItCanUseAzureOpenAIChatClientWithOpenTelemetryAsync()
    {
        // Arrange
        Assert.NotNull(this._configuration.ChatDeploymentName);
        Assert.NotNull(this._configuration.Endpoint);

        // Create a kernel with the AzureOpenAI chat client with OpenTelemetry
        var builder = Kernel.CreateBuilder();
        builder.Services.AddAzureOpenAIChatClient(
            this._configuration.ChatDeploymentName,
            this._configuration.Endpoint,
            new AzureCliCredential(),
            openTelemetrySourceName: "AzureOpenAI.ChatClient.Test");
        var kernel = builder.Build();

        // Act
        var chatClient = kernel.GetRequiredService<IChatClient>();
        var response = await chatClient.GetResponseAsync("List the planets in the solar system");

        // Assert
        Assert.NotNull(response);
        Assert.NotEmpty(response.Text);
        Assert.Contains("Mercury", response.Text, StringComparison.OrdinalIgnoreCase);
    }

    private readonly AzureOpenAIConfiguration _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<AzureOpenAIChatClientTests>()
        .Build()
        .GetSection("AzureOpenAI")
        .Get<AzureOpenAIConfiguration>()!;
}
