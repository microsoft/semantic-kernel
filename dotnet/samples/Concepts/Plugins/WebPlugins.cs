// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Plugins.Web;

namespace Plugins;

/// <summary>
/// Sample showing how to use the Semantic Kernel web plugins correctly.
/// </summary>
public sealed class WebPlugins(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Shows how to download to a temporary directory on the local machine.
    /// </summary>
    [Fact]
    public async Task DownloadSKLogoAsync()
    {
        var uri = new Uri("https://raw.githubusercontent.com/microsoft/semantic-kernel/refs/heads/main/docs/images/sk_logo.png");
        var folderPath = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString());
        var filePath = Path.Combine(folderPath, "sk_logo.png");

        try
        {
            Directory.CreateDirectory(folderPath);

            var webFileDownload = new WebFileDownloadPlugin(this.LoggerFactory)
            {
                AllowedDomains = ["raw.githubusercontent.com"],
                AllowedFolders = [folderPath]
            };

            await webFileDownload.DownloadToFileAsync(uri, filePath);

            if (Path.Exists(filePath))
            {
                Output.WriteLine($"Successfully downloaded to {filePath}");
            }
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
