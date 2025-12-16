// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using Anthropic.Exceptions;

namespace Microsoft.SemanticKernel.Connectors.Anthropic.Core.Extensions;

/// <summary>
/// Provides extension methods for the <see cref="AnthropicApiException"/> class.
/// Follows the same pattern as SK's ClientResultExceptionExtensions for OpenAI.
/// </summary>
[ExcludeFromCodeCoverage]
internal static class AnthropicApiExceptionExtensions
{
    /// <summary>
    /// Converts an <see cref="AnthropicApiException"/> to an <see cref="HttpOperationException"/>.
    /// </summary>
    /// <param name="exception">The original <see cref="AnthropicApiException"/>.</param>
    /// <returns>An <see cref="HttpOperationException"/> instance.</returns>
    /// <remarks>
    /// The Anthropic SDK throws AnthropicApiException for HTTP errors with the following subclasses:
    /// - AnthropicBadRequestException (400)
    /// - AnthropicUnauthorizedException (401)
    /// - AnthropicForbiddenException (403)
    /// - AnthropicNotFoundException (404)
    /// - AnthropicUnprocessableEntityException (422)
    /// - AnthropicRateLimitException (429)
    /// - Anthropic5xxException (5xx)
    /// - AnthropicUnexpectedStatusCodeException (others)
    ///
    /// All of these inherit from AnthropicApiException which has StatusCode and ResponseBody properties.
    /// </remarks>
    public static HttpOperationException ToHttpOperationException(this AnthropicApiException exception)
    {
        if (exception is null)
        {
            throw new ArgumentNullException(nameof(exception));
        }

        // The Anthropic SDK's AnthropicApiException has:
        // - StatusCode (HttpStatusCode) - the HTTP status code
        // - ResponseBody (string) - the raw response body
        // - Message (string) - formatted as "Status Code: {StatusCode}\n{ResponseBody}"
        return new HttpOperationException(
            exception.StatusCode,
            exception.ResponseBody,
            exception.Message,
            exception);
    }
}
