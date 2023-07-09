// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.IO.Compression;
using System.Threading;
using System.Threading.Tasks;

namespace FileCompression;

/// <summary>
/// Implementation of <see cref="IFileCompressor"/> that uses the Zip format.
/// </summary>
public class ZipFileCompressor : IFileCompressor
{
    /// <inheritdoc/>
    public Task CompressDirectoryAsync(string sourceDirectoryPath, string destinationFilePath, CancellationToken cancellationToken)
    {
        return Task.Run(() => ZipFile.CreateFromDirectory(sourceDirectoryPath, destinationFilePath), cancellationToken);
    }

    /// <inheritdoc/>
    public Task CompressFileAsync(string sourceFilePath, string destinationFilePath, CancellationToken cancellationToken)
    {
        return Task.Run(() =>
        {
            using ZipArchive zip = ZipFile.Open(destinationFilePath, ZipArchiveMode.Create);
            zip.CreateEntryFromFile(sourceFilePath, Path.GetFileName(sourceFilePath));
        }, cancellationToken);
    }

    /// <inheritdoc/>
    public async Task DecompressFileAsync(string sourceFilePath, string destinationDirectoryPath, CancellationToken cancellationToken)
    {
        using (ZipArchive archive = await Task.Run(() => ZipFile.OpenRead(sourceFilePath), cancellationToken))
        {
            foreach (ZipArchiveEntry entry in archive.Entries)
            {
                await Task.Run(() => entry.ExtractToFile(Path.Combine(destinationDirectoryPath, entry.FullName)), cancellationToken);
            }
        }
    }
}
