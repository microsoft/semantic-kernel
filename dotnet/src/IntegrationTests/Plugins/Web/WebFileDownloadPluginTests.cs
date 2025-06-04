// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Plugins.Web;
using Xunit;

namespace SemanticKernel.IntegrationTests.Plugins.Web;

/// <summary>
/// Integration tests for <see cref="WebFileDownloadPlugin"/>.
/// </summary>
public sealed class WebFileDownloadPluginTests : BaseIntegrationTest
{
    /// <summary>
    /// Verify downloading to a temporary directory on the local machine.
    /// </summary>
    [Fact]
    public async Task VerifyDownloadToFileAsync()
    {
        var uri = new Uri("https://raw.githubusercontent.com/microsoft/semantic-kernel/refs/heads/main/docs/images/sk_logo.png");
        var folderPath = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString());
        var filePath = Path.Combine(folderPath, "sk_logo.png");

        try
        {
            Directory.CreateDirectory(folderPath);

            var webFileDownload = new WebFileDownloadPlugin()
            {
                AllowedDomains = ["raw.githubusercontent.com"],
                AllowedFolders = [folderPath]
            };

            await webFileDownload.DownloadToFileAsync(uri, filePath);

            Assert.True(Path.Exists(filePath));
        }
        finally
        {
            if (Path.Exists(folderPath))
            {
                Directory.Delete(folderPath, true);
            }
        }
    }
}
