// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Http;

/// <summary>
/// Provides extension methods for working with HTTP content in a way that translates HttpRequestExceptions into HttpOperationExceptions.
/// </summary>
[ExcludeFromCodeCoverage]
internal static class HttpContentExtensions
{
    /// <summary>
    /// Reads the content of the HTTP response as a string and translates any HttpRequestException into an HttpOperationException.
    /// </summary>
    /// <param name="httpContent">The HTTP content to read.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A string representation of the HTTP content.</returns>
    public static async Task<string> ReadAsStringWithExceptionMappingAsync(this HttpContent httpContent, CancellationToken cancellationToken = default)
    {
        try
        {
#if NET5_0_OR_GREATER
            return await httpContent.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
#else
            return await httpContent.ReadAsStringAsync().ConfigureAwait(false);
#endif
        }
        catch (HttpRequestException ex)
        {
            throw new HttpOperationException(message: ex.Message, innerException: ex);
        }
    }

    /// <summary>
    /// Reads the content of the HTTP response as a stream and translates any HttpRequestException into an HttpOperationException.
    /// </summary>
    /// <param name="httpContent">The HTTP content to read.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A stream representing the HTTP content.</returns>
    public static async Task<Stream> ReadAsStreamAndTranslateExceptionAsync(this HttpContent httpContent, CancellationToken cancellationToken = default)
    {
        try
        {
#if NET5_0_OR_GREATER
            return await httpContent.ReadAsStreamAsync(cancellationToken).ConfigureAwait(false);
#else
            return await httpContent.ReadAsStreamAsync().ConfigureAwait(false);
#endif
        }
        catch (HttpRequestException ex)
        {
            throw new HttpOperationException(message: ex.Message, innerException: ex);
        }
    }

    /// <summary>
    /// Reads the content of the HTTP response as a byte array and translates any HttpRequestException into an HttpOperationException.
    /// </summary>
    /// <param name="httpContent">The HTTP content to read.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A byte array representing the HTTP content.</returns>
    public static async Task<byte[]> ReadAsByteArrayAndTranslateExceptionAsync(this HttpContent httpContent, CancellationToken cancellationToken = default)
    {
        try
        {
#if NET5_0_OR_GREATER
            return await httpContent.ReadAsByteArrayAsync(cancellationToken).ConfigureAwait(false);
#else
            return await httpContent.ReadAsByteArrayAsync().ConfigureAwait(false);
#endif
        }
        catch (HttpRequestException ex)
        {
            throw new HttpOperationException(message: ex.Message, innerException: ex);
        }
    }
}
