// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.TextToImage;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

#pragma warning disable CS0618 // Type or member is obsolete

namespace SemanticKernel.IntegrationTests.Connectors.AzureOpenAI;

public sealed class AzureOpenAITextToImageTests
{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<AzureOpenAITextToImageTests>()
        .Build();

    [Fact(Skip = "This test is for manual verification.")]
    public async Task ItCanReturnImageUrlAsync()
    {
        // Arrange
        AzureOpenAIConfiguration? configuration = this._configuration.GetSection("AzureOpenAITextToImage").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(configuration);

        var kernel = Kernel.CreateBuilder()
            .AddAzureOpenAITextToImage(
                deploymentName: configuration.DeploymentName,
                endpoint: configuration.Endpoint,
                credentials: new AzureCliCredential())
            .Build();

        var service = kernel.GetRequiredService<ITextToImageService>();

        // Act
        var result = await service.GenerateImageAsync("The sun rises in the east and sets in the west.", 1024, 1024);

        // Assert
        Assert.NotNull(result);
        Assert.StartsWith("https://", result);
    }

    [Fact]
    public async Task GetImageContentsCanReturnImageUrlAsync()
    {
        // Arrange
        AzureOpenAIConfiguration? configuration = this._configuration.GetSection("AzureOpenAITextToImage").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(configuration);

        var kernel = Kernel.CreateBuilder()
            .AddAzureOpenAITextToImage(
                deploymentName: configuration.DeploymentName,
                endpoint: configuration.Endpoint,
                credentials: new AzureCliCredential())
            .Build();

        var service = kernel.GetRequiredService<ITextToImageService>();

        // Act
        var result = await service.GetImageContentsAsync("The sun rises in the east and sets in the west.", new OpenAITextToImageExecutionSettings { Size = (1024, 1024) });

        // Assert
        Assert.NotNull(result);
        Assert.NotEmpty(result);
        Assert.NotEmpty(result[0].Uri!.ToString());
        Assert.StartsWith("https://", result[0].Uri!.ToString());
    }

    [Fact]
    public async Task SemanticKernelVersionHeaderIsSentAsync()
    {
        // Arrange
        using var defaultHandler = new HttpClientHandler();
        using var httpHeaderHandler = new HttpHeaderHandler(defaultHandler);
        using var httpClient = new HttpClient(httpHeaderHandler);
        AzureOpenAIConfiguration? configuration = this._configuration.GetSection("AzureOpenAITextToImage").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(configuration);

        var kernel = Kernel.CreateBuilder()
            .AddAzureOpenAITextToImage(
                deploymentName: configuration.DeploymentName,
                endpoint: configuration.Endpoint,
                credentials: new AzureCliCredential(),
                httpClient: httpClient)
            .Build();

        var service = kernel.GetRequiredService<ITextToImageService>();

        // Act
        var result = await service.GetImageContentsAsync("The sun rises in the east and sets in the west.", new OpenAITextToImageExecutionSettings { Size = (1024, 1024) });

        // Assert
        Assert.NotNull(result);
        Assert.NotEmpty(result);
        Assert.NotEmpty(result[0].Uri!.ToString());
        Assert.StartsWith("https://", result[0].Uri!.ToString());
        Assert.NotNull(httpHeaderHandler.RequestHeaders);
        Assert.True(httpHeaderHandler.RequestHeaders.TryGetValues("Semantic-Kernel-Version", out var values));
    }

    #region internals

    private sealed class HttpHeaderHandler(HttpMessageHandler innerHandler) : DelegatingHandler(innerHandler)
    {
        public System.Net.Http.Headers.HttpRequestHeaders? RequestHeaders { get; private set; }

        protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            this.RequestHeaders = request.Headers;
            return await base.SendAsync(request, cancellationToken);
        }
    }

    #endregion
}
