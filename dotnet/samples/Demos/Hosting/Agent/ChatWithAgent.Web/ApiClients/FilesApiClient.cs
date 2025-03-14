// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http.Headers;
using Microsoft.AspNetCore.Components.Forms;

namespace ChatWithAgent.Web;

/// <summary>
/// The file API client.
/// </summary>
/// <param name="httpClient">The HTTP client.</param>
internal sealed class FilesApiClient(HttpClient httpClient)
{
    /// <summary>
    /// Uploads files asynchronously.
    /// </summary>
    /// <param name="files">Files to upload.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The completion result.</returns>
    internal async Task UploadFilesAsync(IReadOnlyList<IBrowserFile> files, CancellationToken cancellationToken = default)
    {
        using var content = new MultipartFormDataContent();

        foreach (IBrowserFile file in files)
        {
            var streamContent = new StreamContent(file.OpenReadStream(maxAllowedSize: 20000 * 1024, cancellationToken: cancellationToken));
            streamContent.Headers.ContentType = new MediaTypeHeaderValue(file.ContentType);

            content.Add(streamContent, "files", file.Name);
        }

        var result = await httpClient.PostAsync(new Uri("/files", UriKind.Relative), content, cancellationToken).ConfigureAwait(false);

        result.EnsureSuccessStatusCode();
    }
}
