// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Plugins.Document;
using Microsoft.SemanticKernel.Plugins.Document.FileSystem;
using Microsoft.SemanticKernel.Plugins.Document.OpenXml;
using Xunit;

namespace SemanticKernel.Plugins.UnitTests.Document;

public sealed class LocalFileSystemConnectorTests : IDisposable
{
    private readonly string _directory = Path.Combine(Path.GetTempPath(), $"LocalFileSystemConnectorTests_{Guid.NewGuid():N}");

    public LocalFileSystemConnectorTests()
    {
        Directory.CreateDirectory(this._directory);
    }

    [Fact]
    public async Task DocumentCanBeCreatedAppendedAndReadWithoutLosingExistingTextAsync()
    {
        var path = Path.Combine(this._directory, "document.docx");
        var plugin = new DocumentPlugin(new WordDocumentConnector(), new LocalFileSystemConnector())
        {
            AllowedDirectories = [this._directory]
        };

        await plugin.AppendTextAsync("first paragraph", path);
        await plugin.AppendTextAsync("second paragraph", path);
        var text = await plugin.ReadTextAsync(path);

        Assert.Contains("first paragraph", text);
        Assert.Contains("second paragraph", text);
    }

    [Fact]
    public async Task OpenUpdatePreservesAnExistingEmptyFileAsync()
    {
        var path = Path.Combine(this._directory, "empty.docx");
        File.WriteAllText(path, string.Empty);
        var connector = new LocalFileSystemConnector();

        var opened = await connector.OpenUpdateAsync(path, [this._directory]);
        using var stream = opened.Stream;
        Assert.False(opened.Created);
        Assert.Equal(0, stream.Length);
    }

    [Fact]
    public async Task CancelledOpenDoesNotCreateFileAsync()
    {
        var path = Path.Combine(this._directory, "cancelled.docx");
        var connector = new LocalFileSystemConnector();
        using var cancellation = new CancellationTokenSource();
        cancellation.Cancel();

        await Assert.ThrowsAnyAsync<OperationCanceledException>(
            () => connector.OpenUpdateAsync(path, [this._directory], cancellation.Token));
        Assert.False(File.Exists(path));
    }

    [SymbolicLinkFact]
    public async Task ConnectorRejectsOutsideLinksForReadsAndUpdatesAsync()
    {
        var allowed = Path.Combine(this._directory, "allowed");
        Directory.CreateDirectory(allowed);
        var outside = Path.Combine(this._directory, "outside.txt");
        File.WriteAllText(outside, "unchanged");
        var link = Path.Combine(allowed, "link.txt");
        File.CreateSymbolicLink(link, outside);
        var connector = new LocalFileSystemConnector();

        await Assert.ThrowsAsync<InvalidOperationException>(
            () => connector.GetFileContentStreamAsync(link, [allowed]));
        await Assert.ThrowsAsync<InvalidOperationException>(() => connector.OpenUpdateAsync(link, [allowed]));
        Assert.Equal("unchanged", File.ReadAllText(outside));
    }

    public void Dispose()
    {
        Directory.Delete(this._directory, recursive: true);
    }
}
