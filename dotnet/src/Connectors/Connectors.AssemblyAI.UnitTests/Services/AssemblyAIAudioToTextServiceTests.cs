// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using AssemblyAI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AssemblyAI;
using Xunit;

namespace SemanticKernel.Connectors.AssemblyAI.UnitTests;

/// <summary>
/// Unit tests for <see cref="AssemblyAIAudioToTextService"/> class.
/// </summary>
public sealed class AssemblyAIAudioToTextServiceTests : IDisposable
{
    private const string TranscriptGuid = "0D0446CE-5C41-476F-9642-61F425FEA477";

    private const string UploadFileResponseContent =
        """
        {
            "upload_url": "http://localhost/path/to/file.mp3"
        }
        """;

    private const string CreateTranscriptResponseContent =
        $$"""
          {
            "id": "{{TranscriptGuid}}",
            "language_model": "assemblyai_default",
            "acoustic_model": "assemblyai_default",
            "language_code": "en_us",
            "status": "queued",
            "audio_url": "http://localhost/path/to/file.mp3",
            "text": null,
            "words": null,
            "utterances": null,
            "confidence": null,
            "audio_duration": null,
            "punctuate": true,
            "format_text": true,
            "dual_channel": null,
            "webhook_url": null,
            "webhook_status_code": null,
            "webhook_auth": false,
            "webhook_auth_header_name": null,
            "speed_boost": false,
            "auto_highlights_result": null,
            "auto_highlights": false,
            "audio_start_from": null,
            "audio_end_at": null,
            "word_boost": [],
            "boost_param": null,
            "filter_profanity": false,
            "redact_pii": false,
            "redact_pii_audio": false,
            "redact_pii_audio_quality": null,
            "redact_pii_policies": null,
            "redact_pii_sub": null,
            "speaker_labels": false,
            "content_safety": false,
            "iab_categories": false,
            "content_safety_labels": {},
            "iab_categories_result": {},
            "language_detection": false,
            "language_confidence_threshold": null,
            "language_confidence": null,
            "custom_spelling": null,
            "throttled": false,
            "auto_chapters": false,
            "summarization": false,
            "summary_type": null,
            "summary_model": null,
            "custom_topics": false,
            "topics": [],
            "speech_threshold": null,
            "speech_model": null,
            "chapters": null,
            "disfluencies": false,
            "entity_detection": false,
            "sentiment_analysis": false,
            "sentiment_analysis_results": null,
            "entities": null,
            "speakers_expected": null,
            "summary": null,
            "custom_topics_results": null,
            "is_deleted": null,
            "multichannel": false,
            "audio_channels": null
          }
          """;

    private const string TranscriptCompletedResponseContent =
        $$"""
          {
            "id": "{{TranscriptGuid}}",
            "language_model": "assemblyai_default",
            "acoustic_model": "assemblyai_default",
            "language_code": "en_us",
            "status": "completed",
            "audio_url": "http://localhost/path/to/file.mp3",
            "text": "Test audio-to-text response",
            "words": [
            {
              "start": 120,
              "end": 232,
              "text": "The",
              "confidence": 0.99,
              "speaker": null
            },
            {
              "start": 232,
              "end": 416,
              "text": "sun",
              "confidence": 0.99973,
              "speaker": null
            }
            ],
            "utterances": null,
            "confidence": 0.993280869565217,
            "audio_duration": 6,
            "punctuate": true,
            "format_text": true,
            "dual_channel": null,
            "webhook_url": null,
            "webhook_status_code": null,
            "webhook_auth": false,
            "webhook_auth_header_name": null,
            "speed_boost": false,
            "auto_highlights_result": null,
            "auto_highlights": false,
            "audio_start_from": null,
            "audio_end_at": null,
            "word_boost": [],
            "boost_param": null,
            "filter_profanity": false,
            "redact_pii": false,
            "redact_pii_audio": false,
            "redact_pii_audio_quality": null,
            "redact_pii_policies": null,
            "redact_pii_sub": null,
            "speaker_labels": false,
            "content_safety": false,
            "iab_categories": false,
            "content_safety_labels": {
            "status": "unavailable",
            "results": [],
            "summary": {}
            },
            "iab_categories_result": {
            "status": "unavailable",
            "results": [],
            "summary": {}
            },
            "language_detection": false,
            "language_confidence_threshold": null,
            "language_confidence": null,
            "custom_spelling": null,
            "throttled": false,
            "auto_chapters": false,
            "summarization": false,
            "summary_type": null,
            "summary_model": null,
            "custom_topics": false,
            "topics": [],
            "speech_threshold": null,
            "speech_model": null,
            "chapters": null,
            "disfluencies": false,
            "entity_detection": false,
            "sentiment_analysis": false,
            "sentiment_analysis_results": null,
            "entities": null,
            "speakers_expected": null,
            "summary": null,
            "custom_topics_results": null,
            "is_deleted": null,
            "multichannel": false,
            "audio_channels": 1
          }
          """;

    private const string ExpectedTranscriptText = "Test audio-to-text response";

    private readonly MultipleHttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;

    public AssemblyAIAudioToTextServiceTests()
    {
        this._messageHandlerStub = new MultipleHttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub, false);
    }

    [Fact]
    public void ConstructorWithHttpClientWorksCorrectly()
    {
        // Arrange & Act
        var service = new AssemblyAIAudioToTextService("api-key", httpClient: this._httpClient);

        // Assert
        Assert.NotNull(service);
    }

    [Fact]
    public async Task GetTextContentByDefaultWorksCorrectlyAsync()
    {
        // Arrange
        var service = new AssemblyAIAudioToTextService("api-key", httpClient: this._httpClient);
        using var uploadFileResponse = new HttpResponseMessage(System.Net.HttpStatusCode.OK);
        uploadFileResponse.Content = new StringContent(UploadFileResponseContent);
        using var transcribeResponse = new HttpResponseMessage(System.Net.HttpStatusCode.OK);
        transcribeResponse.Content = new StringContent(CreateTranscriptResponseContent);
        using var transcribedResponse = new HttpResponseMessage(System.Net.HttpStatusCode.OK);
        transcribedResponse.Content = new StringContent(TranscriptCompletedResponseContent);
        this._messageHandlerStub.ResponsesToReturn =
        [
            uploadFileResponse,
            transcribeResponse,
            transcribedResponse
        ];

        // Act
        var result = await service.GetTextContentsAsync(
            new AudioContent(new BinaryData("data").ToMemory(), null)
        ).ConfigureAwait(true);

        // Assert
        Assert.NotNull(result);
        Assert.Single(result);
        Assert.Equal(ExpectedTranscriptText, result[0].Text);
    }

    [Fact]
    public async Task GetTextContentByUrlWorksCorrectlyAsync()
    {
        // Arrange
        var service = new AssemblyAIAudioToTextService("api-key", httpClient: this._httpClient);
        using var transcribeResponse = new HttpResponseMessage(System.Net.HttpStatusCode.OK);
        transcribeResponse.Content = new StringContent(CreateTranscriptResponseContent);
        using var transcribedResponse = new HttpResponseMessage(System.Net.HttpStatusCode.OK);
        transcribedResponse.Content = new StringContent(TranscriptCompletedResponseContent);
        this._messageHandlerStub.ResponsesToReturn = [transcribeResponse, transcribedResponse];

        // Act
        var result = await service.GetTextContentsAsync(
            new AudioContent(new Uri("https://storage.googleapis.com/aai-docs-samples/nbc.mp3"))
        ).ConfigureAwait(true);

        // Assert
        Assert.NotNull(result);
        Assert.Single(result);
        Assert.Equal(ExpectedTranscriptText, result[0].Text);
    }

    [Fact]
    public async Task HttpErrorShouldThrowWithErrorMessageAsync()
    {
        // Arrange
        var service = new AssemblyAIAudioToTextService("api-key", httpClient: this._httpClient);
        using var uploadFileResponse = new HttpResponseMessage(System.Net.HttpStatusCode.InternalServerError);
        this._messageHandlerStub.ResponsesToReturn =
        [
            uploadFileResponse
        ];

        // Act & Assert
        await Assert.ThrowsAsync<ApiException>(
            async () => await service.GetTextContentsAsync(
                new AudioContent(new BinaryData("data").ToMemory(), null)
            ).ConfigureAwait(true)
        ).ConfigureAwait(true);
    }

    [Fact]
    public async Task JsonErrorShouldThrowWithErrorMessageAsync()
    {
        // Arrange
        var service = new AssemblyAIAudioToTextService("api-key", httpClient: this._httpClient);
        using var uploadFileResponse = new HttpResponseMessage(System.Net.HttpStatusCode.Unauthorized);
        const string ErrorMessage = "Bad API key";
        uploadFileResponse.Content = new StringContent(
            $$"""
              {
                  "error": "{{ErrorMessage}}"
              }
              """,
            Encoding.UTF8,
            "application/json"
        );
        this._messageHandlerStub.ResponsesToReturn =
        [
            uploadFileResponse
        ];

        // Act & Assert
        await Assert.ThrowsAsync<ApiException>(
            async () => await service.GetTextContentsAsync(
                new AudioContent(new BinaryData("data").ToMemory(), null)
            ).ConfigureAwait(true)
        ).ConfigureAwait(true);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
