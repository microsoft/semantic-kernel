// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Net.Http;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Http;

/// <summary>
/// Provides extension methods for working with HTTP content in a way that translates HttpRequestExceptions into HttpOperationExceptions.
/// </summary>
internal static class HttpContentExtensions
{
    /// <summary>
    /// Reads the content of the HTTP response as a string and translates any HttpRequestException into an HttpOperationException.
    /// </summary>
    /// <param name="httpContent">The HTTP content to read.</param>
    /// <returns>A string representation of the HTTP content.</returns>
    public static async Task<string> ReadAsStringWithExceptionMappingAsync(this HttpContent httpContent)
    {
        try
        {
            return await httpContent.ReadAsStringAsync().ConfigureAwait(false);
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
    /// <returns>A stream representing the HTTP content.</returns>
    public static async Task<Stream> ReadAsStreamAndTranslateExceptionAsync(this HttpContent httpContent)
    {
        try
        {
            return await httpContent.ReadAsStreamAsync().ConfigureAwait(false);
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
    /// <returns>A byte array representing the HTTP content.</returns>
    public static async Task<byte[]> ReadAsByteArrayAndTranslateExceptionAsync(this HttpContent httpContent)
    {
        try
        {
            return await httpContent.ReadAsByteArrayAsync().ConfigureAwait(false);
        }
        catch (HttpRequestException ex)
        {
            throw new HttpOperationException(message: ex.Message, innerException: ex);
        }
    }
}
