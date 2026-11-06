// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.AI.CrewAI;
using Moq;
using Moq.Protected;
using Xunit;

namespace SemanticKernel.Plugins.AI.UnitTests.CrewAI;

/// <summary>
/// Tests for the <see cref="CrewAIEnterpriseClient"/> class.
/// </summary>
public sealed partial class CrewAIEnterpriseClientTests
{
    private readonly Mock<HttpMessageHandler> _httpMessageHandlerMock;
    private readonly Mock<Func<Task<string>>> _authTokenProviderMock;
    private readonly CrewAIEnterpriseClient _client;

    /// <summary>
    /// Initializes a new instance of the <see cref="CrewAIEnterpriseClientTests"/> class.
    /// </summary>
    public CrewAIEnterpriseClientTests()
    {
        this._httpMessageHandlerMock = new Mock<HttpMessageHandler>();
        this._authTokenProviderMock = new Mock<Func<Task<string>>>();
        this._authTokenProviderMock.Setup(provider => provider()).ReturnsAsync("token");
        using var httpClientFactory = new MockHttpClientFactory(this._httpMessageHandlerMock);
        this._client = new CrewAIEnterpriseClient(
            endpoint: new Uri("http://example.com"),
            authTokenProvider: this._authTokenProviderMock.Object,
            httpClientFactory);
    }

    /// <summary>
    /// Tests that <see cref="CrewAIEnterpriseClient.GetInputsAsync"/> returns the required inputs from the CrewAI API.
    /// </summary>
    /// <returns></returns>
    [Fact]
    public async Task GetInputsAsyncReturnsCrewAIRequiredInputsAsync()
    {
        // Arrange
        var responseContent = "{\"inputs\": [\"input1\", \"input2\"]}";
        using var responseMessage = new HttpResponseMessage
        {
            StatusCode = HttpStatusCode.OK,
            Content = new StringContent(responseContent)
        };

        this._httpMessageHandlerMock.Protected()
            .Setup<Task<HttpResponseMessage>>(
                "SendAsync",
                ItExpr.IsAny<HttpRequestMessage>(),
                ItExpr.IsAny<CancellationToken>())
            .ReturnsAsync(responseMessage);

        // Act
        var result = await this._client.GetInputsAsync();

        // Assert
        Assert.NotNull(result);
        Assert.Equal(2, result.Inputs.Count);
        Assert.Contains("input1", result.Inputs);
        Assert.Contains("input2", result.Inputs);
    }

    /// <summary>
    /// Tests that <see cref="CrewAIEnterpriseClient.KickoffAsync"/> returns the kickoff id from the CrewAI API.
    /// </summary>
    /// <returns></returns>
    [Fact]
    public async Task KickoffAsyncReturnsCrewAIKickoffResponseAsync()
    {
        // Arrange
        var responseContent = "{\"kickoff_id\": \"12345\"}";
        using var responseMessage = new HttpResponseMessage
        {
            StatusCode = HttpStatusCode.OK,
            Content = new StringContent(responseContent)
        };

        this._httpMessageHandlerMock.Protected()
            .Setup<Task<HttpResponseMessage>>(
                "SendAsync",
                ItExpr.IsAny<HttpRequestMessage>(),
                ItExpr.IsAny<CancellationToken>())
            .ReturnsAsync(responseMessage);

        // Act
        var result = await this._client.KickoffAsync(new { key = "value" });

        // Assert
        Assert.NotNull(result);
        Assert.Equal("12345", result.KickoffId);
    }

    /// <summary>
    /// Tests that <see cref="CrewAIEnterpriseClient.GetStatusAsync"/> returns the status of the CrewAI Crew.
    /// </summary>
    /// <param name="state"></param>
    /// <returns></returns>
    /// <exception cref="ArgumentOutOfRangeException"></exception>
    [Theory]
    [InlineData(CrewAIKickoffState.Pending)]
    [InlineData(CrewAIKickoffState.Started)]
    [InlineData(CrewAIKickoffState.Running)]
    [InlineData(CrewAIKickoffState.Success)]
    [InlineData(CrewAIKickoffState.Failed)]
    [InlineData(CrewAIKickoffState.Failure)]
    [InlineData(CrewAIKickoffState.NotFound)]
    public async Task GetStatusAsyncReturnsCrewAIStatusResponseAsync(CrewAIKickoffState state)
    {
        var crewAIStatusState = state switch
        {
            CrewAIKickoffState.Pending => "PENDING",
            CrewAIKickoffState.Started => "STARTED",
            CrewAIKickoffState.Running => "RUNNING",
            CrewAIKickoffState.Success => "SUCCESS",
            CrewAIKickoffState.Failed => "FAILED",
            CrewAIKickoffState.Failure => "FAILURE",
            CrewAIKickoffState.NotFound => "NOT FOUND",
            _ => throw new ArgumentOutOfRangeException(nameof(state), state, null)
        };

        // Arrange
        var responseContent = $"{{\"state\": \"{crewAIStatusState}\", \"result\": \"The Result\", \"last_step\": {{\"step1\": \"value1\"}}}}";
        using var responseMessage = new HttpResponseMessage
        {
            StatusCode = HttpStatusCode.OK,
            Content = new StringContent(responseContent)
        };

        this._httpMessageHandlerMock.Protected()
            .Setup<Task<HttpResponseMessage>>(
                "SendAsync",
                ItExpr.IsAny<HttpRequestMessage>(),
                ItExpr.IsAny<CancellationToken>())
            .ReturnsAsync(responseMessage);

        // Act
        var result = await this._client.GetStatusAsync("12345");

        // Assert
        Assert.NotNull(result);
        Assert.Equal(state, result.State);
        Assert.Equal("The Result", result.Result);
        Assert.NotNull(result.LastStep);
        Assert.Equal("value1", result.LastStep["step1"].ToString());
    }

    /// <summary>
    /// Verifies that valid task identifiers are preserved in the status request path.
    /// </summary>
    [Theory]
    [InlineData("12345")]
    [InlineData("AZaz09_-")]
    [InlineData("640f9a3a-2734-4ba8-8b8a-2f796f419d03")]
    public async Task GetStatusAsyncPreservesValidTaskIdAsync(string taskId)
    {
        using var responseMessage = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent("{\"state\":\"SUCCESS\",\"result\":\"The Result\"}")
        };

        this._httpMessageHandlerMock.Protected()
            .Setup<Task<HttpResponseMessage>>(
                "SendAsync",
                ItExpr.Is<HttpRequestMessage>(request =>
                    request.RequestUri!.AbsolutePath == $"/status/{taskId}"),
                ItExpr.IsAny<CancellationToken>())
            .ReturnsAsync(responseMessage);

        var result = await this._client.GetStatusAsync(taskId);

        Assert.Equal(CrewAIKickoffState.Success, result.State);
        Assert.Equal("The Result", result.Result);
        this._httpMessageHandlerMock.Protected().Verify(
            "SendAsync",
            Times.Once(),
            ItExpr.Is<HttpRequestMessage>(request =>
                request.RequestUri!.AbsoluteUri == $"http://example.com/status/{taskId}"),
            ItExpr.IsAny<CancellationToken>());
    }

    /// <summary>
    /// Verifies that invalid task identifiers are rejected before requesting credentials or sending HTTP requests.
    /// </summary>
    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData(" ")]
    [InlineData("task.id")]
    [InlineData("task/id")]
    [InlineData(@"task\id")]
    [InlineData("task%id")]
    [InlineData("task?id")]
    [InlineData("task#id")]
    [InlineData("task id")]
    [InlineData("task\n")]
    [InlineData("task\r\n")]
    [InlineData("task\t")]
    [InlineData("task\u0000")]
    [InlineData("t\u00E1sk")]
    [InlineData("\uFF11\uFF12\uFF13")]
    public async Task GetStatusAsyncRejectsInvalidTaskIdBeforeAuthenticationAsync(string? taskId)
    {
        var exception = await Assert.ThrowsAsync<KernelException>(
            () => this._client.GetStatusAsync(taskId!));

        var argumentException = Assert.IsAssignableFrom<ArgumentException>(exception.InnerException);
        Assert.Equal("taskId", argumentException.ParamName);
        this._authTokenProviderMock.Verify(provider => provider(), Times.Never());
        this._httpMessageHandlerMock.Protected().Verify(
            "SendAsync",
            Times.Never(),
            ItExpr.IsAny<HttpRequestMessage>(),
            ItExpr.IsAny<CancellationToken>());
    }
}
