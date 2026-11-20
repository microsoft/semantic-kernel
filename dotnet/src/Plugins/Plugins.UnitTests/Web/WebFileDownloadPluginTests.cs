// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Runtime.InteropServices;
using System.Threading;
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

        var webFileDownload = new WebFileDownloadPlugin(this._httpClient)
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
        await using var server = new RedirectLoopbackServer("secret.png", "image/png", [0x89, 0x50, 0x4E, 0x47]);

        var folderPath = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString());
        var filePath = Path.Combine(folderPath, "file.png");
        Directory.CreateDirectory(folderPath);

        var webFileDownload = new WebFileDownloadPlugin()
        {
            AllowedDomains = [server.BaseUri.Host],
            AllowedFolders = [folderPath]
        };

        try
        {
            // Act & Assert - the plugin should throw because 302 is a non-success status
            await Assert.ThrowsAsync<HttpOperationException>(() => webFileDownload.DownloadToFileAsync(new Uri(server.BaseUri, "start"), filePath));
            Assert.False(server.RedirectTargetContacted, "The redirect target should not have been contacted.");
            Assert.False(Path.Exists(filePath));
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

        var webFileDownload = new WebFileDownloadPlugin(this._httpClient)
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

    [Theory]
    [InlineData("\\\\UNC\\server\\folder\\myfile.txt")]
    [InlineData("//UNC/server/folder/myfile.txt")]
    [InlineData("/\\UNC\\server\\folder\\myfile.txt")]
    [InlineData("\\/UNC/server/folder/myfile.txt")]
    public async Task DownloadToFileRejectsUncOrExtendedPathsAsync(string filePath)
    {
        // Arrange
        var uri = new Uri("https://raw.githubusercontent.com/microsoft/semantic-kernel/refs/heads/main/docs/images/sk_logo.png");
        var folderPath = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString());
        var webFileDownload = new WebFileDownloadPlugin()
        {
            AllowedDomains = ["raw.githubusercontent.com"],
            AllowedFolders = [folderPath]
        };

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentException>(() => webFileDownload.DownloadToFileAsync(uri, filePath));
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

    [SymbolicLinkTheory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task DownloadRejectsLinksReplacedDuringRequestAsync(bool replaceParent)
    {
        var directory = Path.Combine(Path.GetTempPath(), $"WebFileDownloadPluginTests_{Guid.NewGuid():N}");
        var allowed = Path.Combine(directory, "allowed");
        var parent = Path.Combine(allowed, "parent");
        var outsideDirectory = Path.Combine(directory, "outside");
        Directory.CreateDirectory(parent);
        Directory.CreateDirectory(outsideDirectory);
        var path = Path.Combine(parent, "file.txt");
        var outside = Path.Combine(outsideDirectory, "file.txt");
        await File.WriteAllTextAsync(path, "allowed");
        await File.WriteAllTextAsync(outside, "outside");
        try
        {
            using var handler = new CallbackHandler(() =>
            {
                if (replaceParent)
                {
                    Directory.Move(parent, parent + "-original");
                    Directory.CreateSymbolicLink(parent, outsideDirectory);
                }
                else
                {
                    File.Delete(path);
                    File.CreateSymbolicLink(path, outside);
                }

                return new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent("replacement") };
            });
            using var client = new HttpClient(handler);
            var plugin = new WebFileDownloadPlugin(client)
            {
                AllowedDomains = ["localhost"],
                AllowedFolders = [allowed],
                DisableFileOverwrite = false
            };

            await Assert.ThrowsAsync<InvalidOperationException>(
                () => plugin.DownloadToFileAsync(new Uri("http://localhost/file"), path));
            Assert.Equal("outside", await File.ReadAllTextAsync(outside));
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    [Fact]
    public async Task DownloadDoesNotOverwriteFileCreatedDuringRequestAsync()
    {
        var directory = Path.Combine(Path.GetTempPath(), $"WebFileDownloadPluginTests_{Guid.NewGuid():N}");
        Directory.CreateDirectory(directory);
        var path = Path.Combine(directory, "file.txt");
        try
        {
            using var handler = new CallbackHandler(() =>
            {
                File.WriteAllText(path, "created during request");
                return new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent("replacement") };
            });
            using var client = new HttpClient(handler);
            var plugin = new WebFileDownloadPlugin(client)
            {
                AllowedDomains = ["localhost"],
                AllowedFolders = [directory]
            };

            var error = await Assert.ThrowsAsync<InvalidOperationException>(
                () => plugin.DownloadToFileAsync(new Uri("http://localhost/file"), path));
            Assert.Contains("Overwriting", error.Message);
            Assert.Equal("created during request", await File.ReadAllTextAsync(path));
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    [Theory]
    [InlineData(HttpStatusCode.Forbidden, 10)]
    [InlineData(HttpStatusCode.OK, 1)]
    public async Task RejectedResponseDoesNotTruncateDestinationAsync(HttpStatusCode status, int maximumSize)
    {
        var directory = Path.Combine(Path.GetTempPath(), $"WebFileDownloadPluginTests_{Guid.NewGuid():N}");
        Directory.CreateDirectory(directory);
        var path = Path.Combine(directory, "file.txt");
        await File.WriteAllTextAsync(path, "unchanged");
        try
        {
            using var handler = new CallbackHandler(() => new HttpResponseMessage(status)
            {
                Content = new StringContent("oversize")
            });
            using var client = new HttpClient(handler);
            var plugin = new WebFileDownloadPlugin(client)
            {
                AllowedDomains = ["localhost"],
                AllowedFolders = [directory],
                DisableFileOverwrite = false,
                MaximumDownloadSize = maximumSize
            };

            await Assert.ThrowsAnyAsync<Exception>(
                () => plugin.DownloadToFileAsync(new Uri("http://localhost/file"), path));
            Assert.Equal("unchanged", await File.ReadAllTextAsync(path));
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    private sealed class CallbackHandler(Func<HttpResponseMessage> responseFactory) : HttpMessageHandler
    {
        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken) =>
            Task.FromResult(responseFactory());
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
