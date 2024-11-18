// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// Proxy that leverages a chat client to generate the request body payload before calling the target concrete function.
/// </summary>
internal sealed class RestApiOperationRunnerPayloadProxy : IRestApiOperationRunner
{
    private readonly RestApiOperationRunner _concrete;
    private readonly IChatClient _chatClient;

    /// <summary>
    /// Initializes a new instance of the <see cref="RestApiOperationRunnerPayloadProxy"/> class.
    /// </summary>
    /// <param name="concrete">Operation runner to call with the generated payload</param>
    /// <param name="chatClient">Chat client to generate the payload</param>
    /// <exception cref="ArgumentNullException">If the provided Operation runner argument is null</exception>
    public RestApiOperationRunnerPayloadProxy(RestApiOperationRunner concrete, IChatClient chatClient)
    {
        Verify.NotNull(concrete);
        Verify.NotNull(chatClient);
        this._concrete = concrete;
        this._chatClient = chatClient;
        if (concrete.EnableDynamicPayload)
        {
            throw new InvalidOperationException("The concrete operation runner must not support dynamic payloads.");
        }
    }

    /// <inheritdoc />
    public async Task<RestApiOperationResponse> RunAsync(RestApiOperation operation, KernelArguments arguments, RestApiOperationRunOptions? options = null, CancellationToken cancellationToken = default)
    {
        var url = this._concrete.BuildsOperationUrl(operation, arguments, options?.ServerUrlOverride, options?.ApiHostUrl);

        var headers = operation.BuildHeaders(arguments);

        var operationPayload = await this.BuildOperationPayloadAsync(operation, arguments, cancellationToken).ConfigureAwait(false);

        return await this._concrete.SendAsync(url, operation.Method, headers, operationPayload.Payload, operationPayload.Content, operation.Responses.ToDictionary(static item => item.Key, static item => item.Value.Schema), options, cancellationToken).ConfigureAwait(false);
    }
    /// <summary>
    /// Builds operation payload.
    /// </summary>
    /// <param name="operation">The operation.</param>
    /// <param name="arguments">The operation payload arguments.</param>
    /// <returns>The raw operation payload and the corresponding HttpContent.</returns>
    private Task<(object? Payload, HttpContent? Content)> BuildOperationPayloadAsync(RestApiOperation operation, IDictionary<string, object?> arguments, CancellationToken cancellationToken)
    {
        if (operation.Payload is null && !arguments.ContainsKey(RestApiOperation.PayloadArgumentName))
        {
            return Task.FromResult<(object?, HttpContent?)>((null, null));
        }

        var mediaType = operation.Payload?.MediaType;
        if (string.IsNullOrEmpty(mediaType))
        {
            if (!arguments.TryGetValue(RestApiOperation.ContentTypeArgumentName, out object? fallback) || fallback is not string mediaTypeFallback)
            {
                throw new KernelException($"No media type is provided for the {operation.Id} operation.");
            }

            mediaType = mediaTypeFallback;
        }

        if (!RestApiOperationRunner.MediaTypeApplicationJson.Equals(mediaType!, StringComparison.OrdinalIgnoreCase))
        {
            throw new KernelException($"The media type {mediaType} of the {operation.Id} operation is not supported by {nameof(RestApiOperationRunnerPayloadProxy)}.");
        }

        return this.BuildJsonPayloadAsync(operation.Payload, arguments, cancellationToken);
    }
    /// <summary>
    /// Builds "application/json" payload.
    /// </summary>
    /// <param name="payloadMetadata">The payload meta-data.</param>
    /// <param name="arguments">The payload arguments.</param>
    /// <returns>The JSON payload the corresponding HttpContent.</returns>
    private async Task<(object? Payload, HttpContent? Content)> BuildJsonPayloadAsync(RestApiPayload? payloadMetadata, IDictionary<string, object?> arguments, CancellationToken cancellationToken)
    {
        string message =
        """
        Given the following JSON schema, and the following context, generate the JSON payload:
        """;
        //TODO get the schema from the arguments, and the context

        var completion = await this._chatClient.CompleteAsync(message, cancellationToken: cancellationToken).ConfigureAwait(false);
        var content = completion.Message.Text;
        return (content, new StringContent(content, Encoding.UTF8, RestApiOperationRunner.MediaTypeApplicationJson));
    }
}
