// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Azure.Core;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Services;
using Moq;

namespace SemanticKernel.Connectors.AzureOpenAI.UnitTests.Services;

/// <summary>
/// Unit tests for <see cref="AzureOpenAIAudioToTextService"/> class.
/// </summary>
public sealed class AzureOpenAIAudioToTextServiceTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;
    private readonly Mock<ILoggerFactory> _mockLoggerFactory;

    public AzureOpenAIAudioToTextServiceTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub, false);
        this._mockLoggerFactory = new Mock<ILoggerFactory>();
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void ConstructorWithApiKeyWorksCorrectly(bool includeLoggerFactory)
    {
        // Arrange & Act
        var service = includeLoggerFactory ?
            new AzureOpenAIAudioToTextService("deployment", "https://endpoint", "api-key", "model-id", loggerFactory: this._mockLoggerFactory.Object) :
            new AzureOpenAIAudioToTextService("deployment", "https://endpoint", "api-key", "model-id");

        // Assert
        Assert.Equal("model-id", service.Attributes[AIServiceExtensions.ModelIdKey]);
        Assert.Equal("deployment", service.Attributes[AzureClientCore.DeploymentNameKey]);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void ConstructorWithTokenCredentialWorksCorrectly(bool includeLoggerFactory)
    {
        // Arrange & Act
        var credentials = DelegatedTokenCredential.Create((_, _) => new AccessToken());
        var service = includeLoggerFactory ?
            new AzureOpenAIAudioToTextService("deployment", "https://endpoint", credentials, "model-id", loggerFactory: this._mockLoggerFactory.Object) :
            new AzureOpenAIAudioToTextService("deployment", "https://endpoint", credentials, "model-id");

        // Assert
        Assert.Equal("model-id", service.Attributes[AIServiceExtensions.ModelIdKey]);
        Assert.Equal("deployment", service.Attributes[AzureClientCore.DeploymentNameKey]);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void ConstructorWithOpenAIClientWorksCorrectly(bool includeLoggerFactory)
    {
        // Arrange & Act
        var client = new AzureOpenAIClient(new Uri("http://host"), new ApiKeyCredential("key"));
        var service = includeLoggerFactory ?
            new AzureOpenAIAudioToTextService("deployment", client, "model-id", loggerFactory: this._mockLoggerFactory.Object) :
            new AzureOpenAIAudioToTextService("deployment", client, "model-id");

        // Assert
        Assert.Equal("model-id", service.Attributes[AIServiceExtensions.ModelIdKey]);
        Assert.Equal("deployment", service.Attributes[AzureClientCore.DeploymentNameKey]);
    }

    [Fact]
    public void ItThrowsIfDeploymentNameIsNotProvided()
    {
        // Act & Assert
        Assert.Throws<ArgumentException>(() => new AzureOpenAIAudioToTextService(" ", "http://host", "apikey"));
        Assert.Throws<ArgumentException>(() => new AzureOpenAIAudioToTextService(" ", azureOpenAIClient: new(new Uri("http://host"), new ApiKeyCredential("apikey"))));
        Assert.Throws<ArgumentException>(() => new AzureOpenAIAudioToTextService("", "http://host", "apikey"));
        Assert.Throws<ArgumentException>(() => new AzureOpenAIAudioToTextService("", azureOpenAIClient: new(new Uri("http://host"), new ApiKeyCredential("apikey"))));
        Assert.Throws<ArgumentNullException>(() => new AzureOpenAIAudioToTextService(null!, "http://host", "apikey"));
        Assert.Throws<ArgumentNullException>(() => new AzureOpenAIAudioToTextService(null!, azureOpenAIClient: new(new Uri("http://host"), new ApiKeyCredential("apikey"))));
    }

    [Theory]
    [MemberData(nameof(ExecutionSettings))]
    public async Task GetTextContentWithInvalidSettingsThrowsExceptionAsync(OpenAIAudioToTextExecutionSettings? settings, Type expectedExceptionType)
    {
        // Arrange
        var service = new AzureOpenAIAudioToTextService("deployment", "https://endpoint", "api-key", "model-id", this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent("Test audio-to-text response")
        };

        // Act
        var exception = await Record.ExceptionAsync(() => service.GetTextContentsAsync(new AudioContent(new BinaryData("data"), mimeType: null), settings));

        // Assert
        Assert.NotNull(exception);
        Assert.IsType(expectedExceptionType, exception);
    }

    [Theory]
    [InlineData("verbose_json")]
    [InlineData("json")]
    [InlineData("vtt")]
    [InlineData("srt")]
    public async Task ItRespectResultFormatExecutionSettingAsync(string format)
    {
        // Arrange
        var service = new AzureOpenAIAudioToTextService("deployment", "https://endpoint", "api-key", httpClient: this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent("Test audio-to-text response")
        };

        // Act
        var settings = new OpenAIAudioToTextExecutionSettings("file.mp3") { ResponseFormat = format };
        var result = await service.GetTextContentsAsync(new AudioContent(new BinaryData("data"), mimeType: null), settings);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        Assert.NotNull(result);

        var multiPartData = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        var multiPartBreak = multiPartData.Substring(0, multiPartData.IndexOf("\r\n", StringComparison.OrdinalIgnoreCase));

        Assert.Contains($"{format}\r\n{multiPartBreak}", multiPartData);
    }

    [Fact]
    public async Task GetTextContentByDefaultWorksCorrectlyAsync()
    {
        // Arrange
        var service = new AzureOpenAIAudioToTextService("deployment-name", "https://endpoint", "api-key", "model-id", this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent("Test audio-to-text response")
        };

        // Act
        var result = await service.GetTextContentsAsync(new AudioContent(new BinaryData("data"), mimeType: null), new OpenAIAudioToTextExecutionSettings("file.mp3"));

        // Assert
        Assert.NotNull(result);
        Assert.Equal("Test audio-to-text response", result[0].Text);
    }

    [Theory]
    [MemberData(nameof(Versions))]
    public async Task ItTargetsApiVersionAsExpected(string? apiVersion, string? expectedVersion = null)
    {
        // Arrange
        var service = new AzureOpenAIAudioToTextService("deployment", "https://endpoint", "api-key", httpClient: this._httpClient, apiVersion: apiVersion);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent("Test audio-to-text response")
        };

        // Act
        var settings = new OpenAIAudioToTextExecutionSettings("file.mp3");
        var result = await service.GetTextContentsAsync(new AudioContent(new BinaryData("data"), mimeType: null), settings);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        Assert.NotNull(result);

        Assert.Contains($"api-version={expectedVersion}", this._messageHandlerStub.RequestUri!.ToString());
    }

    [Theory]
    [InlineData(new[] { "word" }, new[] { "word" })]
    [InlineData(new[] { "word", "Word", "wOrd", "Segment" }, new[] { "word", "segment" })]
    [InlineData(new[] { "Word", "Segment" }, new[] { "word", "segment" })]
    [InlineData(new[] { "Segment" }, new[] { "segment" })]
    [InlineData(new[] { "Segment", "wOrd" }, new[] { "word", "segment" })]
    [InlineData(new[] { "WORD" }, new[] { "word" })]
    [InlineData(new string[] { }, null)]
    [InlineData(null, null)]
    public async Task GetTextContentGranularitiesWorksCorrectlyAsync(string[]? granularities, string[]? expectedGranularities)
    {
        // Arrange
        var service = new AzureOpenAIAudioToTextService("deployment", "https://endpoint", "api-key", httpClient: this._httpClient);

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent("Test audio-to-text response")
        };

        // Act
        var result = await service.GetTextContentsAsync(new AudioContent(new BinaryData("data"), mimeType: null), new OpenAIAudioToTextExecutionSettings("file.mp3")
        {
            ResponseFormat = "verbose_json",
            TimestampGranularities = granularities
        });

        // Assert
        var requestBody = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        if (granularities is null || granularities.Length == 0)
        {
            Assert.DoesNotContain("timestamp_granularities[]", requestBody);
        }
        else
        {
            foreach (var granularity in expectedGranularities!)
            {
                Assert.Contains($"Content-Disposition: form-data; name=\"timestamp_granularities[]\"\r\n\r\n{granularity}", requestBody);
            }
        }
    }

    public static TheoryData<string?, string?> Versions => new()
    {
        { "V2024_10_01_preview", "2024-10-01-preview" },
        { "V2024_10_01_PREVIEW", "2024-10-01-preview" },
        { "2024_10_01_Preview", "2024-10-01-preview" },
        { "2024-10-01-preview", "2024-10-01-preview" },
        { "V2024_08_01_preview", "2024-08-01-preview" },
        { "V2024_08_01_PREVIEW", "2024-08-01-preview" },
        { "2024_08_01_Preview", "2024-08-01-preview" },
        { "2024-08-01-preview", "2024-08-01-preview" },
        { "V2024_06_01", "2024-06-01" },
        { "2024_06_01", "2024-06-01" },
        { "2024-06-01", "2024-06-01" },
        { AzureOpenAIClientOptions.ServiceVersion.V2024_10_01_Preview.ToString(), null },
        { AzureOpenAIClientOptions.ServiceVersion.V2024_08_01_Preview.ToString(), null },
        { AzureOpenAIClientOptions.ServiceVersion.V2024_06_01.ToString(), null }
    };

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }

    public static TheoryData<OpenAIAudioToTextExecutionSettings?, Type> ExecutionSettings => new()
    {
        { new OpenAIAudioToTextExecutionSettings(""), typeof(ArgumentException) },
        { new OpenAIAudioToTextExecutionSettings("file"), typeof(ArgumentException) }
    };
}
