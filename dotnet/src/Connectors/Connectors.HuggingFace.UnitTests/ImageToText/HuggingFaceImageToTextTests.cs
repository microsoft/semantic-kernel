// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.HuggingFace;
using Microsoft.SemanticKernel.ImageToText;
using Xunit;

namespace SemanticKernel.Connectors.HuggingFace.UnitTests;

/// <summary>
/// Unit tests for <see cref="HuggingFaceImageToTextService"/> class.
/// </summary>
public sealed class HuggingFaceImageToTextTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;
    private readonly ImageContent _imageContentInput;

    public HuggingFaceImageToTextTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(HuggingFaceTestHelper.GetTestResponse("imagetotext_test_response.json"));

        this._httpClient = new HttpClient(this._messageHandlerStub, false);

        var expectedPayload = HuggingFaceTestHelper.GetTestResponseBytes("imagetotext_test_request.jpg");
#pragma warning disable SKEXP0015
        this._imageContentInput = new ImageContent(expectedPayload, "model") { MimeType = "image/jpeg" };
#pragma warning restore SKEXP0015
    }

    [Fact]
    public async Task SpecifiedModelShouldBeUsedAsync()
    {
        //Arrange
        var sut = new HuggingFaceImageToTextService("fake-model", httpClient: this._httpClient);

        //Act
        await sut.GetTextContentsAsync(this._imageContentInput);

        //Assert
        Assert.EndsWith("/fake-model", this._messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task NoAuthorizationHeaderShouldBeAddedIfApiKeyIsNotProvidedAsync()
    {
        //Arrange
        var sut = new HuggingFaceImageToTextService("fake-model", apiKey: null, httpClient: this._httpClient);

        //Act
        await sut.GetTextContentsAsync(this._imageContentInput);

        //Assert
        Assert.False(this._messageHandlerStub.RequestHeaders?.Contains("Authorization"));
    }

    [Fact]
    public async Task AuthorizationHeaderShouldBeAddedIfApiKeyIsProvidedAsync()
    {
        //Arrange
        var sut = new HuggingFaceImageToTextService("fake-model", apiKey: "fake-api-key", httpClient: this._httpClient);

        //Act
        await sut.GetTextContentsAsync(this._imageContentInput);

        //Assert
        Assert.True(this._messageHandlerStub.RequestHeaders?.Contains("Authorization"));

        var values = this._messageHandlerStub.RequestHeaders!.GetValues("Authorization");

        var value = values.SingleOrDefault();
        Assert.Equal("Bearer fake-api-key", value);
    }

    [Fact]
    public async Task UserAgentHeaderShouldBeUsedAsync()
    {
        //Arrange
        var sut = new HuggingFaceImageToTextService("fake-model", httpClient: this._httpClient);

        //Act
        await sut.GetTextContentsAsync(this._imageContentInput);

        //Assert
        Assert.True(this._messageHandlerStub.RequestHeaders?.Contains("User-Agent"));

        var values = this._messageHandlerStub.RequestHeaders!.GetValues("User-Agent");

        var value = values.SingleOrDefault();
        Assert.Equal("Semantic-Kernel", value);
    }

    [Fact]
    public async Task ProvidedEndpointShouldBeUsedAsync()
    {
        //Arrange
        var sut = new HuggingFaceImageToTextService("fake-model", endpoint: new Uri("https://fake-random-test-host/fake-path"), httpClient: this._httpClient);

        //Act
        await sut.GetTextContentsAsync(this._imageContentInput);

        //Assert
        Assert.StartsWith("https://fake-random-test-host/fake-path", this._messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task HttpClientBaseAddressShouldBeUsedAsync()
    {
        //Arrange
        this._httpClient.BaseAddress = new Uri("https://fake-random-test-host/fake-path");

        var sut = new HuggingFaceImageToTextService("fake-model", httpClient: this._httpClient);

        //Act
        await sut.GetTextContentsAsync(this._imageContentInput);

        //Assert
        Assert.StartsWith("https://fake-random-test-host/fake-path", this._messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task DefaultAddressShouldBeUsedAsync()
    {
        //Arrange
        var sut = new HuggingFaceImageToTextService("fake-model", httpClient: this._httpClient);

        //Act
        await sut.GetTextContentsAsync(this._imageContentInput);

        //Assert
        Assert.StartsWith("https://api-inference.huggingface.co/models", this._messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task ModelUrlShouldBeBuiltSuccessfullyAsync()
    {
        //Arrange
        var sut = new HuggingFaceImageToTextService("fake-model", endpoint: new Uri("https://fake-random-test-host/fake-path"), httpClient: this._httpClient);

        //Act
        await sut.GetTextContentsAsync(this._imageContentInput);

        //Assert
        Assert.Equal("https://fake-random-test-host/fake-path/models/fake-model", this._messageHandlerStub.RequestUri?.AbsoluteUri);
    }

    [Fact]
    public async Task ShouldSendPromptToServiceAsync()
    {
        //Arrange
        var sut = new HuggingFaceImageToTextService("fake-model", httpClient: this._httpClient);

        //Act
        await sut.GetTextContentsAsync(this._imageContentInput);

        //Assert
        var requestPayload = this._messageHandlerStub.RequestContent;

        Assert.NotNull(requestPayload);
        Assert.Equal(this._imageContentInput.Data!.Value.Span, requestPayload);
    }

    [Fact]
    public async Task ShouldHandleServiceResponseAsync()
    {
        //Arrange
        var sut = new HuggingFaceImageToTextService("fake-model", endpoint: new Uri("https://fake-random-test-host/fake-path"), httpClient: this._httpClient);
        var expectedPayload = HuggingFaceTestHelper.GetTestResponseBytes("imagetotext_test_request.jpg");

        //Act
        var contents = await sut.GetTextContentsAsync(this._imageContentInput);

        //Assert
        Assert.NotNull(contents);

        var content = contents.SingleOrDefault();
        Assert.NotNull(content);
        Assert.Equal("This is test completion response", content.Text);
    }

    [Fact]
    public async Task GetTextContentsShouldHaveModelIdDefinedAsync()
    {
        //Arrange
        var sut = new HuggingFaceImageToTextService("fake-model", endpoint: new Uri("https://fake-random-test-host/fake-path"), httpClient: this._httpClient);

        //Act
        var contents = await sut.GetTextContentsAsync(this._imageContentInput);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent(@"
            [
                {
                    ""generated_text"": ""Why the sky is blue? | Dept. of Science & Mathematics Education | University of Notre Dame\nWhen I was in high school I had a pretty simple conception of reality. I believed that if something made sense to me, then it must also be true. I believed that some problems were so fundamental that I couldn’t understand""
                }
            ]",
            Encoding.UTF8,
            "application/json")
        };

        // Act
        var textContent = await sut.GetTextContentAsync(this._imageContentInput);

        // Assert
        Assert.NotNull(textContent.ModelId);
        Assert.Equal("fake-model", textContent.ModelId);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
