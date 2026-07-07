// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Net.Http;
using System.Runtime.InteropServices;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
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
    public async Task DownloadToFileDoesNotFollowRedirectsAsync()
    {
        // Arrange - start a local server that returns a 302 redirect
        using var listener = new System.Net.HttpListener();
        var port = new Random().Next(49152, 65535);
        listener.Prefixes.Add($"http://localhost:{port}/");
        listener.Start();
        bool redirectTargetContacted = false;

        _ = Task.Run(async () =>
        {
            while (listener.IsListening)
            {
                try
                {
                    var ctx = await listener.GetContextAsync();
                    if (ctx.Request.Url!.AbsolutePath == "/start")
                    {
                        ctx.Response.StatusCode = 302;
                        ctx.Response.RedirectLocation = $"http://localhost:{port}/secret.png";
                        ctx.Response.Close();
                    }
                    else if (ctx.Request.Url.AbsolutePath == "/secret.png")
                    {
                        redirectTargetContacted = true;
                        ctx.Response.StatusCode = 200;
                        ctx.Response.ContentType = "image/png";
                        ctx.Response.OutputStream.Write(new byte[] { 0x89, 0x50, 0x4E, 0x47 });
                        ctx.Response.Close();
                    }
                }
                catch (ObjectDisposedException) { break; }
                catch (System.Net.HttpListenerException) { break; }
            }
        });

        var folderPath = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString());
        var filePath = Path.Combine(folderPath, "file.png");
        Directory.CreateDirectory(folderPath);

        var webFileDownload = new WebFileDownloadPlugin()
        {
            AllowedDomains = ["localhost"],
            AllowedFolders = [folderPath]
        };

        try
        {
            // Act & Assert - the plugin should throw because 302 is a non-success status
            await Assert.ThrowsAsync<HttpOperationException>(() => webFileDownload.DownloadToFileAsync(new Uri($"http://localhost:{port}/start"), filePath));
            Assert.False(redirectTargetContacted, "The redirect target should not have been contacted.");
            Assert.False(Path.Exists(filePath));
        }
        finally
        {
            listener.Stop();
            if (Path.Exists(folderPath))
            {
                Directory.Delete(folderPath, true);
            }
        }
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
        await Assert.ThrowsAsync<ArgumentException>(async () => await webFileDownload.DownloadToFileAsync(validUri, "//UNC/server/folder/myfile.txt"));
        await Assert.ThrowsAsync<ArgumentException>(async () => await webFileDownload.DownloadToFileAsync(validUri, "//?/C:/Windows/win.ini"));
        await Assert.ThrowsAsync<ArgumentException>(async () => await webFileDownload.DownloadToFileAsync(validUri, ""));
        // Relative paths are now canonicalized to absolute paths via Path.GetFullPath,
        // so they are caught by the AllowedFolders check rather than the "fully qualified" check.
        await Assert.ThrowsAsync<InvalidOperationException>(async () => await webFileDownload.DownloadToFileAsync(validUri, "myfile.txt"));
    }

    [Fact]
    public async Task DownloadToFileUsesCaseSensitiveAllowListComparisonOnLinuxAsync()
    {
        if (!RuntimeInformation.IsOSPlatform(OSPlatform.Linux))
        {
            return;
        }

        // Arrange
        this._messageHandlerStub.AddImageResponse(File.ReadAllBytes(SKLogoPng));
        var uri = new Uri("https://raw.githubusercontent.com/microsoft/semantic-kernel/refs/heads/main/docs/images/sk_logo.png");
        var tempDir = Path.Combine(Path.GetTempPath(), $"WebFileDownloadPluginTests_{Guid.NewGuid():N}");
        var allowedDir = Path.Combine(tempDir, "Allowed");
        var disallowedDir = Path.Combine(tempDir, "allowed");
        Directory.CreateDirectory(allowedDir);
        Directory.CreateDirectory(disallowedDir);

        try
        {
            var webFileDownload = new WebFileDownloadPlugin()
            {
                AllowedDomains = ["raw.githubusercontent.com"],
                AllowedFolders = [allowedDir]
            };

            var disallowedFile = Path.Combine(disallowedDir, "download.txt");

            // Act & Assert
            await Assert.ThrowsAsync<InvalidOperationException>(() => webFileDownload.DownloadToFileAsync(uri, disallowedFile));
        }
        finally
        {
            if (Path.Exists(tempDir))
            {
                Directory.Delete(tempDir, true);
            }
        }
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
