// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

internal static class DocumentLoader
{
    internal static async Task<string> LoadDocumentFromUriAsync(
        Uri uri,
        ILogger logger,
        HttpClient httpClient,
        AuthenticateRequestAsyncCallback? authCallback,
        string? userAgent,
        CancellationToken cancellationToken)
    {
        using var response = await LoadDocumentResponseFromUriAsync(uri, logger, httpClient, authCallback, userAgent, cancellationToken).ConfigureAwait(false);
        return await response.Content.ReadAsStringWithExceptionMappingAsync(cancellationToken).ConfigureAwait(false);
    }

    internal static async Task<Stream> LoadDocumentFromUriAsStreamAsync(
        Uri uri,
        ILogger logger,
        HttpClient httpClient,
        AuthenticateRequestAsyncCallback? authCallback,
        string? userAgent,
        CancellationToken cancellationToken)
    {
        //disposing the response disposes the stream
        var response = await LoadDocumentResponseFromUriAsync(uri, logger, httpClient, authCallback, userAgent, cancellationToken).ConfigureAwait(false);
        var stream = await response.Content.ReadAsStreamAndTranslateExceptionAsync(cancellationToken).ConfigureAwait(false);
        return new HttpResponseStream(stream, response);
    }

    private static async Task<HttpResponseMessage> LoadDocumentResponseFromUriAsync(
        Uri uri,
        ILogger logger,
        HttpClient httpClient,
        AuthenticateRequestAsyncCallback? authCallback,
        string? userAgent,
        CancellationToken cancellationToken)
    {
        using var request = new HttpRequestMessage(HttpMethod.Get, uri.ToString());
        request.Headers.UserAgent.Add(ProductInfoHeaderValue.Parse(userAgent ?? HttpHeaderConstant.Values.UserAgent));

        if (authCallback is not null)
        {
            await authCallback(request, cancellationToken).ConfigureAwait(false);
        }

        logger.LogTrace("Importing document from '{Uri}'", uri);

        return await httpClient.SendWithSuccessCheckAsync(request, cancellationToken).ConfigureAwait(false);
    }

    internal static async Task<string> LoadDocumentFromFilePathAsync(
        string filePath,
        ILogger logger,
        CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();

        CheckIfFileExists(filePath, logger);

        logger.LogTrace("Importing document from '{FilePath}'", filePath);

        using var sr = File.OpenText(filePath);
        return await sr.ReadToEndAsync(
#if NET
            cancellationToken
#endif
            ).ConfigureAwait(false);
    }

    private static void CheckIfFileExists(string filePath, ILogger logger)
    {
        if (!File.Exists(filePath))
        {
            var exception = new FileNotFoundException($"Invalid file path. The specified path '{filePath}' does not exist.");
            logger.LogError(exception, "Invalid file path. The specified path '{FilePath}' does not exist.", filePath);
            throw exception;
        }
    }

    internal static Stream LoadDocumentFromFilePathAsStream(
        string filePath,
        ILogger logger)
    {
        CheckIfFileExists(filePath, logger);

        logger.LogTrace("Importing document from {0}", filePath);

        return File.OpenRead(filePath);
    }

    internal static async Task<string> LoadDocumentFromStreamAsync(
        Stream stream,
        CancellationToken cancellationToken)
    {
        using StreamReader reader = new(stream);
#if NET
        return await reader.ReadToEndAsync(cancellationToken).ConfigureAwait(false);
#else
        return await reader.ReadToEndAsync().ConfigureAwait(false);
#endif
    }
}
