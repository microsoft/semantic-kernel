// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Plugins.Web;
using Xunit;

namespace SemanticKernel.Plugins.UnitTests.Web;

/// <summary>
/// Unit tests for <see cref="WebFileDownloadPlugin"/>
/// </summary>
public sealed class WebFileDownloadPluginTests : IDisposable
{
    /// <summary>
    /// Initializes a new instance of the <see cref="WebFileDownloadPluginTests"/> class.
    /// </summary>
    public WebFileDownloadPluginTests()
    {
        this._messageHandlerStub = new MultipleHttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub, disposeHandler: false);
    }

    [Fact]
    public async Task DownloadToFileSucceedsAsync()
    {
        // Arrange
        this._messageHandlerStub.AddImageResponse(File.ReadAllBytes(SKLogoPng));
        var uri = new Uri("https://raw.githubusercontent.com/microsoft/semantic-kernel/refs/heads/main/docs/images/sk_logo.png");
        var folderPath = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString());
        var filePath = Path.Combine(folderPath, "sk_logo.png");
        Directory.CreateDirectory(folderPath);

        var webFileDownload = new WebFileDownloadPlugin()
        {
            AllowedDomains = ["raw.githubusercontent.com"],
            AllowedFolders = [folderPath]
        };

        try
        {
            // Act
            await webFileDownload.DownloadToFileAsync(uri, filePath);

            // Assert
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

    [Fact]
    public async Task DownloadToFileFailsForInvalidDomainAsync()
    {
        // Arrange
        this._messageHandlerStub.AddImageResponse(File.ReadAllBytes(SKLogoPng));
        var uri = new Uri("https://raw.githubfakecontent.com/microsoft/semantic-kernel/refs/heads/main/docs/images/sk_logo.png");
        var folderPath = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString());
        var filePath = Path.Combine(folderPath, "sk_logo.png");
        Directory.CreateDirectory(folderPath);

        var webFileDownload = new WebFileDownloadPlugin()
        {
            AllowedDomains = ["raw.githubusercontent.com"],
            AllowedFolders = [folderPath]
        };

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(async () => await webFileDownload.DownloadToFileAsync(uri, filePath));
    }

    [Fact]
    public async Task DownloadToFileDeniesAllWithDefaultConfigAsync()
    {
        // Arrange
        this._messageHandlerStub.AddImageResponse(File.ReadAllBytes(SKLogoPng));
        var uri = new Uri("https://raw.githubusercontent.com/microsoft/semantic-kernel/refs/heads/main/docs/images/sk_logo.png");
        var folderPath = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString());
        var filePath = Path.Combine(folderPath, "sk_logo.png");
        Directory.CreateDirectory(folderPath);

        var webFileDownload = new WebFileDownloadPlugin();

        try
        {
            // Act & Assert - default config denies all domains
            await Assert.ThrowsAsync<InvalidOperationException>(async () => await webFileDownload.DownloadToFileAsync(uri, filePath));
        }
        finally
        {
            if (Path.Exists(folderPath))
            {
                Directory.Delete(folderPath, true);
            }
        }
    }

    [Fact]
    public void ValidatePluginProperties()
    {
        // Arrange & Act - verify secure defaults
        var defaultPlugin = new WebFileDownloadPlugin();

        // Assert - defaults are deny-all
        Assert.Empty(defaultPlugin.AllowedDomains!);
        Assert.Empty(defaultPlugin.AllowedFolders!);
        Assert.True(defaultPlugin.DisableFileOverwrite);
        Assert.Equal(10 * 1024 * 1024, defaultPlugin.MaximumDownloadSize);

        // Arrange & Act - verify explicit configuration
        var folderPath = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString());

        var webFileDownload = new WebFileDownloadPlugin()
        {
            AllowedDomains = ["raw.githubusercontent.com"],
            AllowedFolders = [folderPath],
            MaximumDownloadSize = 100,
            DisableFileOverwrite = true
        };

        // Assert
        Assert.Equal(["raw.githubusercontent.com"], webFileDownload.AllowedDomains);
        Assert.Equal([folderPath], webFileDownload.AllowedFolders);
        Assert.Equal(100, webFileDownload.MaximumDownloadSize);
        Assert.True(webFileDownload.DisableFileOverwrite);
    }

    [Fact]
    public async Task DownloadToFileFailsForInvalidParametersAsync()
    {
        // Arrange
        this._messageHandlerStub.AddImageResponse(File.ReadAllBytes(SKLogoPng));
        var validUri = new Uri("https://raw.githubusercontent.com/microsoft/semantic-kernel/refs/heads/main/docs/images/sk_logo.png");
        var invalidUri = new Uri("https://raw.githubfakecontent.com/microsoft/semantic-kernel/refs/heads/main/docs/images/sk_logo.png");
        var folderPath = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString());
        var validFilePath = Path.Combine(folderPath, "sk_logo.png");
        var invalidFilePath = Path.Combine(Path.GetTempPath(), "sk_logo.png");
        Directory.CreateDirectory(folderPath);

        var webFileDownload = new WebFileDownloadPlugin()
        {
            AllowedDomains = ["raw.githubusercontent.com"],
            AllowedFolders = [folderPath],
            MaximumDownloadSize = 100
        };

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(async () => await webFileDownload.DownloadToFileAsync(validUri, validFilePath));
        await Assert.ThrowsAsync<InvalidOperationException>(async () => await webFileDownload.DownloadToFileAsync(invalidUri, validFilePath));
        await Assert.ThrowsAsync<InvalidOperationException>(async () => await webFileDownload.DownloadToFileAsync(validUri, invalidFilePath));
        await Assert.ThrowsAsync<ArgumentException>(async () => await webFileDownload.DownloadToFileAsync(validUri, "\\\\UNC\\server\\folder\\myfile.txt"));
        await Assert.ThrowsAsync<ArgumentException>(async () => await webFileDownload.DownloadToFileAsync(validUri, ""));
        // Relative paths are now canonicalized to absolute paths via Path.GetFullPath,
        // so they are caught by the AllowedFolders check rather than the "fully qualified" check.
        await Assert.ThrowsAsync<InvalidOperationException>(async () => await webFileDownload.DownloadToFileAsync(validUri, "myfile.txt"));
    }

    /// <inheritdoc/>
    public void Dispose()
    {
        this._messageHandlerStub.Dispose();
        this._httpClient.Dispose();
        GC.SuppressFinalize(this);
    }

    #region private
    private const string SKLogoPng = "./TestData/sk_logo.png";

    private readonly MultipleHttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;
    #endregion
}
