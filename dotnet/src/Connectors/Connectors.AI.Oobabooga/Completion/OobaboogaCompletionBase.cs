// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Net.WebSockets;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.AI.Oobabooga.Completion;

/// <summary>
/// Base class for Oobabooga completion with common scaffolding shared between Text and Chat completions and generic parameters corresponding to the various types used in Text and Chat completions.
/// </summary>
public abstract class OobaboogaCompletionBase<TCompletionInput, TRequestSettings, TOobaboogaParameters, TCompletionRequest, TCompletionResponse, TCompletionResult, TCompletionStreamingResult> : OobaboogaCompletionBase
    where TCompletionStreamingResult : CompletionStreamingResultBase, new()
    where TOobaboogaParameters : OobaboogaCompletionParameters, new()

{
    /// <summary>
    /// Initializes a new instance of the <see cref="OobaboogaCompletionBase"/> class.
    /// </summary>
    /// <param name="oobaboogaSettings">The settings controlling how calls to the Oobabooga server are made</param>
    protected OobaboogaCompletionBase(OobaboogaCompletionSettings<TOobaboogaParameters>? oobaboogaSettings = default) : base(oobaboogaSettings ?? new())
    {
    }

    protected async Task<IReadOnlyList<TCompletionResult>> GetCompletionsBaseAsync(
        TCompletionInput input,
        TRequestSettings? requestSettings,
        CancellationToken cancellationToken = default)
    {
        try
        {
            await this.OobaboogaSettings.StartConcurrentCallAsync(cancellationToken).ConfigureAwait(false);

            var completionRequest = this.CreateCompletionRequest(input, requestSettings);

            using var httpRequestMessage = HttpRequest.CreatePostRequest(this.OobaboogaSettings.BlockingUri, completionRequest);
            httpRequestMessage.Headers.Add("User-Agent", Telemetry.HttpUserAgent);

            using var response = await this.OobaboogaSettings.HttpClient.SendAsync(httpRequestMessage, cancellationToken).ConfigureAwait(false);
            response.EnsureSuccessStatusCode();

            var body = await response.Content.ReadAsStringAsync().ConfigureAwait(false);

            TCompletionResponse? completionResponse = JsonSerializer.Deserialize<TCompletionResponse>(body);

            if (completionResponse is null)
            {
                throw new SKException($"Unexpected response from Oobabooga API:\n{body}");
            }

            return this.GetCompletionResults(completionResponse);
        }
        catch (Exception e) when (e is not AIException && !e.IsCriticalException())
        {
            throw new AIException(
                AIException.ErrorCodes.UnknownError,
                $"Something went wrong: {e.Message}", e);
        }
        finally
        {
            this.OobaboogaSettings.FinishConcurrentCall();
        }
    }

    protected async IAsyncEnumerable<TCompletionStreamingResult> GetStreamingCompletionsBaseAsync(
        TCompletionInput input,
        TRequestSettings? requestSettings,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await this.OobaboogaSettings.StartConcurrentCallAsync(cancellationToken).ConfigureAwait(false);

        var completionRequest = this.CreateCompletionRequest(input, requestSettings);

        var requestJson = JsonSerializer.Serialize(completionRequest);

        var requestBytes = Encoding.UTF8.GetBytes(requestJson);

        ClientWebSocket? clientWebSocket = null;
        try
        {
            // if pooling is enabled, web socket is going to be recycled for reuse, if not it will be properly disposed of after the call
#pragma warning disable CA2000 // Dispose objects before losing scope
            if (!this.OobaboogaSettings.UseWebSocketsPooling || !this.OobaboogaSettings.WebSocketPool.TryTake(out clientWebSocket))
            {
                clientWebSocket = this.OobaboogaSettings.WebSocketFactory();
            }
#pragma warning restore CA2000 // Dispose objects before losing scope
            if (clientWebSocket.State == WebSocketState.None)
            {
                await clientWebSocket.ConnectAsync(this.OobaboogaSettings.StreamingUri, cancellationToken).ConfigureAwait(false);
            }

            var sendSegment = new ArraySegment<byte>(requestBytes);
            await clientWebSocket.SendAsync(sendSegment, WebSocketMessageType.Text, true, cancellationToken).ConfigureAwait(false);

            TCompletionStreamingResult streamingResult = new();

            var processingTask = this.ProcessWebSocketMessagesAsync(clientWebSocket, streamingResult, cancellationToken);

            yield return streamingResult;

            // Await the processing task to make sure it's finished before continuing
            await processingTask.ConfigureAwait(false);
        }
        finally
        {
            if (clientWebSocket != null)
            {
                if (this.OobaboogaSettings.UseWebSocketsPooling && clientWebSocket.State == WebSocketState.Open)
                {
                    this.OobaboogaSettings.WebSocketPool.Add(clientWebSocket);
                }
                else
                {
                    await this.OobaboogaSettings.DisposeClientGracefullyAsync(clientWebSocket).ConfigureAwait(false);
                }
            }

            this.OobaboogaSettings.FinishConcurrentCall();
        }
    }

    protected abstract IReadOnlyList<TCompletionResult> GetCompletionResults([DisallowNull] TCompletionResponse completionResponse);

    protected abstract TCompletionRequest CreateCompletionRequest(TCompletionInput input, TRequestSettings? requestSettings);
}

/// <summary>
/// Base class for Oobabooga completion with common scaffolding shared between Text and Chat completion
/// </summary>
public abstract class OobaboogaCompletionBase
{
    private protected readonly OobaboogaCompletionSettings OobaboogaSettings;

    /// <summary>
    /// Initializes a new instance of the <see cref="OobaboogaCompletionBase"/> class.
    /// </summary>
    /// <param name="oobaboogaSettings">The settings controlling how calls to the Oobabooga server are made</param>
    protected OobaboogaCompletionBase(OobaboogaCompletionSettings oobaboogaSettings)
    {
        this.OobaboogaSettings = oobaboogaSettings;
    }

    /// <summary>
    /// That method is responsible for processing the websocket messages that build a streaming response object. It is crucial that it is run asynchronously to prevent a deadlock with results iteration
    /// </summary>
    protected async Task ProcessWebSocketMessagesAsync(ClientWebSocket clientWebSocket, CompletionStreamingResultBase streamingResult, CancellationToken cancellationToken)
    {
        var buffer = new byte[this.OobaboogaSettings.WebSocketBufferSize];
        var finishedProcessing = false;
        while (!finishedProcessing && !cancellationToken.IsCancellationRequested)
        {
            MemoryStream messageStream = new();
            WebSocketReceiveResult result;
            do
            {
                var segment = new ArraySegment<byte>(buffer);
                result = await clientWebSocket.ReceiveAsync(segment, cancellationToken).ConfigureAwait(false);
                await messageStream.WriteAsync(buffer, 0, result.Count, cancellationToken).ConfigureAwait(false);
            } while (!result.EndOfMessage);

            messageStream.Seek(0, SeekOrigin.Begin);

            if (result.MessageType == WebSocketMessageType.Text)
            {
                string messageText;
                using (var reader = new StreamReader(messageStream, Encoding.UTF8))
                {
                    messageText = await reader.ReadToEndAsync().ConfigureAwait(false);
                }

                var responseObject = this.GetResponseObject(messageText);

                if (responseObject is null)
                {
                    throw new SKException($"Unexpected response from Oobabooga API: {messageText}");
                }

                switch (responseObject.Event)
                {
                    case CompletionStreamingResponseBase.ResponseObjectTextStreamEvent:
                        streamingResult.AppendResponse(responseObject);
                        break;
                    case CompletionStreamingResponseBase.ResponseObjectStreamEndEvent:
                        streamingResult.SignalStreamEnd();
                        if (!this.OobaboogaSettings.UseWebSocketsPooling)
                        {
                            await clientWebSocket.CloseAsync(WebSocketCloseStatus.NormalClosure, "Acknowledge stream-end oobabooga message", CancellationToken.None).ConfigureAwait(false);
                        }

                        finishedProcessing = true;
                        break;
                }
            }
            else if (result.MessageType == WebSocketMessageType.Close)
            {
                await clientWebSocket.CloseOutputAsync(WebSocketCloseStatus.NormalClosure, "Acknowledge Close frame", CancellationToken.None).ConfigureAwait(false);
                finishedProcessing = true;
            }

            if (clientWebSocket.State != WebSocketState.Open)
            {
                finishedProcessing = true;
            }
        }
    }

    protected abstract CompletionStreamingResponseBase? GetResponseObject(string messageText);

    #region private ================================================================================

    /// <summary>
    /// Logs Oobabooga action details.
    /// </summary>
    /// <param name="callerMemberName">Caller member name. Populated automatically by runtime.</param>
    private protected void LogActionDetails([CallerMemberName] string? callerMemberName = default)
    {
        this.OobaboogaSettings.Logger?.LogInformation("Oobabooga Action: {Action}.", callerMemberName);
    }

    #endregion
}
