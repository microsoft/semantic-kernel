// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices;
using System.Runtime.Versioning;
using System.Text;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.Plugins.UnitTests.Core;

public sealed class SecureFileSystemTests : IDisposable
{
    private readonly string _tempDirectory;
    private readonly string _allowedDirectory;
    private readonly string _outsideDirectory;

    public SecureFileSystemTests()
    {
        this._tempDirectory = Path.Combine(
            Path.GetTempPath(),
            $"SecureFileSystemTests_{Guid.NewGuid():N}");
        this._allowedDirectory = Path.Combine(this._tempDirectory, "allowed");
        this._outsideDirectory = Path.Combine(this._tempDirectory, "outside");

        Directory.CreateDirectory(this._allowedDirectory);
        Directory.CreateDirectory(this._outsideDirectory);
    }

    [Fact]
    public void OpenReadReadsFileInsideAllowedDirectory()
    {
        // Arrange
        var filePath = Path.Combine(this._allowedDirectory, "input.txt");
        File.WriteAllText(filePath, "allowed content");

        // Act
        using var stream = SecureFileSystem.OpenRead(
            filePath,
            [this._allowedDirectory],
            out var resolvedPath);
        using var reader = new StreamReader(stream);

        // Assert
        Assert.Equal("allowed content", reader.ReadToEnd());
        Assert.Equal(PathUtilities.GetSafeFullPath(filePath), resolvedPath);
    }

    [Fact]
    public void OpenReadRejectsFileOutsideAllowedDirectory()
    {
        // Arrange
        var filePath = Path.Combine(this._outsideDirectory, "outside.txt");
        File.WriteAllText(filePath, "outside content");

        // Act and assert
        var exception = Assert.Throws<InvalidOperationException>(
            () => SecureFileSystem.OpenRead(filePath, [this._allowedDirectory], out _));

        Assert.Contains("not within allowed directories", exception.Message);
    }

    [SymbolicLinkFact]
    public void OpenReadRejectsSymbolicLinkToFileOutsideAllowedDirectory()
    {
        // Arrange
        var outsideFile = Path.Combine(this._outsideDirectory, "outside.txt");
        var linkPath = Path.Combine(this._allowedDirectory, "link.txt");
        File.WriteAllText(outsideFile, "outside content");

        File.CreateSymbolicLink(linkPath, outsideFile);

        // Act and assert
        Assert.Throws<InvalidOperationException>(
            () => SecureFileSystem.OpenRead(linkPath, [this._allowedDirectory], out _));
    }

    [SymbolicLinkFact]
    public void OpenReadRejectsSymbolicLinkDirectoryToFileOutsideAllowedDirectory()
    {
        // Arrange
        var outsideFile = Path.Combine(this._outsideDirectory, "outside.txt");
        var linkDirectory = Path.Combine(this._allowedDirectory, "linked-directory");
        File.WriteAllText(outsideFile, "outside content");

        Directory.CreateSymbolicLink(linkDirectory, this._outsideDirectory);

        // Act and assert
        Assert.Throws<InvalidOperationException>(
            () => SecureFileSystem.OpenRead(
                Path.Combine(linkDirectory, "outside.txt"),
                [this._allowedDirectory],
                out _));
    }

    [Fact]
    public void OpenWriteCreatesFileInsideAllowedDirectory()
    {
        // Arrange
        var filePath = Path.Combine(this._allowedDirectory, "new.txt");
        var content = Encoding.UTF8.GetBytes("new content");

        // Act
        using (var stream = SecureFileSystem.OpenWrite(
            filePath,
            [this._allowedDirectory],
            out var resolvedPath))
        {
            stream.Write(content, 0, content.Length);
            Assert.Equal(PathUtilities.GetSafeFullPath(filePath), resolvedPath);
        }

        // Assert
        Assert.Equal("new content", File.ReadAllText(filePath));
    }

    [Fact]
    public void OpenWriteTruncatesExistingFileInsideAllowedDirectory()
    {
        // Arrange
        var filePath = Path.Combine(this._allowedDirectory, "existing.txt");
        var content = Encoding.UTF8.GetBytes("short");
        File.WriteAllText(filePath, "existing longer content");

        // Act
        using (var stream = SecureFileSystem.OpenWrite(
            filePath,
            [this._allowedDirectory],
            out _))
        {
            stream.Write(content, 0, content.Length);
        }

        // Assert
        Assert.Equal("short", File.ReadAllText(filePath));
    }

    [SymbolicLinkFact]
    public void OpenWriteRejectsSymbolicLinkToFileOutsideAllowedDirectory()
    {
        // Arrange
        var outsideFile = Path.Combine(this._outsideDirectory, "outside.txt");
        var linkPath = Path.Combine(this._allowedDirectory, "link.txt");
        File.WriteAllText(outsideFile, "must not change");

        File.CreateSymbolicLink(linkPath, outsideFile);

        // Act
        Assert.Throws<InvalidOperationException>(
            () => SecureFileSystem.OpenWrite(linkPath, [this._allowedDirectory], out _));

        // Assert
        Assert.Equal("must not change", File.ReadAllText(outsideFile));
    }

    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public void EmptyAllowedDirectoriesDenyReadsAndWrites(bool useNull)
    {
        var path = Path.Combine(this._allowedDirectory, "denied.txt");
        string[]? allowed = useNull ? null : [];

        Assert.Throws<InvalidOperationException>(() => SecureFileSystem.OpenRead(path, allowed, out _));
        Assert.Throws<InvalidOperationException>(() => SecureFileSystem.OpenWrite(path, allowed, out _));
        Assert.Throws<InvalidOperationException>(() => SecureFileSystem.OpenUpdate(path, allowed, out _));
        Assert.False(File.Exists(path));
    }

    [Theory]
    [InlineData(@"\\server\share\file.txt")]
    [InlineData("//server/share/file.txt")]
    [InlineData(@"/\server\share\file.txt")]
    [InlineData(@"\/server/share/file.txt")]
    [InlineData(@"\\?\C:\file.txt")]
    [InlineData(@"\\.\device")]
    public void NetworkAndDevicePathsAreRejected(string path)
    {
        Assert.Throws<ArgumentException>(() => SecureFileSystem.OpenRead(path, [this._allowedDirectory], out _));
        Assert.Throws<ArgumentException>(() => SecureFileSystem.OpenWrite(path, [this._allowedDirectory], out _));
    }

    [Fact]
    public void RootDirectoryCanBeAllowed()
    {
        var path = Path.Combine(this._allowedDirectory, "root.txt");
        File.WriteAllText(path, "content");

        using var stream = SecureFileSystem.OpenRead(path, [Path.GetPathRoot(path)!], out _);
        using var reader = new StreamReader(stream);
        Assert.Equal("content", reader.ReadToEnd());
    }

    [Fact]
    public void DirectoryWithMatchingNamePrefixIsNotAllowed()
    {
        var directory = this._allowedDirectory + "-outside";
        Directory.CreateDirectory(directory);
        var path = Path.Combine(directory, "file.txt");
        File.WriteAllText(path, "unchanged");

        Assert.Throws<InvalidOperationException>(() => SecureFileSystem.OpenRead(path, [this._allowedDirectory], out _));
        Assert.Throws<InvalidOperationException>(() => SecureFileSystem.OpenWrite(path, [this._allowedDirectory], out _));
        Assert.Equal("unchanged", File.ReadAllText(path));
    }

    [Fact]
    public void CreateNewDoesNotOverwriteExistingFile()
    {
        var path = Path.Combine(this._allowedDirectory, "existing.txt");
        File.WriteAllText(path, "unchanged");

        Assert.Throws<SecureFileSystem.FileAlreadyExistsException>(
            () => SecureFileSystem.OpenWrite(path, [this._allowedDirectory], out _, FileMode.CreateNew));
        Assert.Equal("unchanged", File.ReadAllText(path));
    }

    [Fact]
    public void CreateNewCreatesMissingFile()
    {
        var path = Path.Combine(this._allowedDirectory, "new.txt");
        using (var stream = SecureFileSystem.OpenWrite(path, [this._allowedDirectory], out _, FileMode.CreateNew))
        {
            stream.WriteByte(42);
        }

        Assert.Equal(new byte[] { 42 }, File.ReadAllBytes(path));
    }

    [Fact]
    public void OpenUpdateReportsCreationWithoutTruncatingExistingFiles()
    {
        var path = Path.Combine(this._allowedDirectory, "document.txt");
        using (var stream = SecureFileSystem.OpenUpdate(path, [this._allowedDirectory], out var created))
        {
            Assert.True(created);
            Assert.True(stream.CanRead);
            Assert.True(stream.CanWrite);
            Assert.True(stream.CanSeek);
            stream.WriteByte(42);
        }

        using (var stream = SecureFileSystem.OpenUpdate(path, [this._allowedDirectory], out var created))
        {
            Assert.False(created);
            Assert.Equal(42, stream.ReadByte());
        }
    }

    [Fact]
    public void OpenUpdateDoesNotTreatAnExistingEmptyFileAsNew()
    {
        var path = Path.Combine(this._allowedDirectory, "empty.txt");
        File.WriteAllText(path, string.Empty);
        using var stream = SecureFileSystem.OpenUpdate(path, [this._allowedDirectory], out var created);
        Assert.False(created);
    }

    [Fact]
    public void WritesToReadOnlyFilesAreRejectedBeforeTruncation()
    {
        var path = Path.Combine(this._allowedDirectory, "readonly.txt");
        File.WriteAllText(path, "unchanged");
        File.SetAttributes(path, FileAttributes.ReadOnly);
        try
        {
            Assert.Throws<UnauthorizedAccessException>(
                () => SecureFileSystem.OpenWrite(path, [this._allowedDirectory], out _));
            Assert.Throws<UnauthorizedAccessException>(
                () => SecureFileSystem.OpenUpdate(path, [this._allowedDirectory], out _));
            Assert.Equal("unchanged", File.ReadAllText(path));
        }
        finally
        {
            File.SetAttributes(path, FileAttributes.Normal);
        }
    }

    [SymbolicLinkTheory]
    [InlineData(false, false)]
    [InlineData(false, true)]
    [InlineData(true, false)]
    [InlineData(true, true)]
    public void LinkReplacementAfterCanonicalizationIsRejected(bool write, bool replaceParent)
    {
        var parent = Path.Combine(this._allowedDirectory, "parent");
        Directory.CreateDirectory(parent);
        var path = Path.Combine(parent, "file.txt");
        var outside = Path.Combine(this._outsideDirectory, "file.txt");
        File.WriteAllText(path, "allowed");
        File.WriteAllText(outside, "outside");

        IEnumerable<string> AllowedDirectories()
        {
            yield return this._outsideDirectory;
            // The first comparison has already resolved the caller's path. Replace a
            // component before returning the allowed folder used by the native open.
            if (replaceParent)
            {
                Directory.Move(parent, parent + "-original");
                Directory.CreateSymbolicLink(parent, this._outsideDirectory);
            }
            else
            {
                File.Move(path, path + ".original");
                File.CreateSymbolicLink(path, outside);
            }

            yield return this._allowedDirectory;
        }

        if (write)
        {
            Assert.Throws<InvalidOperationException>(
                () => SecureFileSystem.OpenWrite(path, AllowedDirectories(), out _));
        }
        else
        {
            Assert.Throws<InvalidOperationException>(
                () => SecureFileSystem.OpenRead(path, AllowedDirectories(), out _));
        }

        Assert.Equal("outside", File.ReadAllText(outside));
        var original = replaceParent ? Path.Combine(parent + "-original", "file.txt") : path + ".original";
        Assert.Equal("allowed", File.ReadAllText(original));
    }

    [SymbolicLinkFact]
    public void ExistingLinkToAllowedFileCanBeRead()
    {
        var target = Path.Combine(this._allowedDirectory, "target.txt");
        var link = Path.Combine(this._allowedDirectory, "link.txt");
        File.WriteAllText(target, "allowed");
        File.CreateSymbolicLink(link, target);
        using var stream = SecureFileSystem.OpenRead(link, [this._allowedDirectory], out _);
        using var reader = new StreamReader(stream);
        Assert.Equal("allowed", reader.ReadToEnd());
    }

    [SymbolicLinkTheory]
    [InlineData(false)]
    [InlineData(true)]
    public void OpenStreamCannotBeRedirectedByReplacingItsName(bool write)
    {
        var path = Path.Combine(this._allowedDirectory, "file.txt");
        var original = path + ".original";
        var outside = Path.Combine(this._outsideDirectory, "file.txt");
        File.WriteAllText(path, "allowed");
        File.WriteAllText(outside, "outside");
        using (var stream = write
            ? SecureFileSystem.OpenWrite(path, [this._allowedDirectory], out _)
            : SecureFileSystem.OpenRead(path, [this._allowedDirectory], out _))
        {
            if (OperatingSystem.IsWindows())
            {
                Assert.Throws<IOException>(() => File.Move(path, original));
            }
            else
            {
                File.Move(path, original);
                File.CreateSymbolicLink(path, outside);
            }

            if (write)
            {
                stream.WriteByte(42);
            }
            else
            {
                using var reader = new StreamReader(stream, leaveOpen: true);
                Assert.Equal("allowed", reader.ReadToEnd());
            }
        }

        Assert.Equal("outside", File.ReadAllText(outside));
        if (write)
        {
            Assert.Equal(new byte[] { 42 }, File.ReadAllBytes(OperatingSystem.IsWindows() ? path : original));
        }
    }

    [Fact]
    public void MissingParentIsNotCreated()
    {
        var path = Path.Combine(this._allowedDirectory, "missing", "file.txt");
        Assert.Throws<FileNotFoundException>(() => SecureFileSystem.OpenWrite(path, [this._allowedDirectory], out _));
        Assert.False(Directory.Exists(Path.GetDirectoryName(path)));
    }

    [LinuxNonRootTheory]
    [InlineData(false)]
    [InlineData(true)]
    [SupportedOSPlatform("linux")]
    public void SearchOnlyDirectoriesDoNotPreventFileAccess(bool restrictedAncestorOfAllowedRoot)
    {
        var restricted = Path.Combine(this._tempDirectory, "search-only");
        var writable = Path.Combine(restricted, "writable");
        Directory.CreateDirectory(writable);
        var allowed = restrictedAncestorOfAllowedRoot ? writable : restricted;
        var input = Path.Combine(writable, "input.txt");
        var output = Path.Combine(writable, "output.txt");
        File.WriteAllText(input, "readable");
        var originalMode = File.GetUnixFileMode(restricted);
        try
        {
            File.SetUnixFileMode(restricted,
                UnixFileMode.UserExecute | UnixFileMode.GroupExecute | UnixFileMode.OtherExecute);
            Assert.Equal("readable", File.ReadAllText(input));
            Assert.Throws<UnauthorizedAccessException>(() => Directory.GetFileSystemEntries(restricted));

            using (var stream = SecureFileSystem.OpenRead(input, [allowed], out _))
            using (var reader = new StreamReader(stream))
            {
                Assert.Equal("readable", reader.ReadToEnd());
            }

            using (var stream = SecureFileSystem.OpenWrite(output, [allowed], out _, FileMode.CreateNew))
            {
                stream.WriteByte(42);
            }

            using (var stream = SecureFileSystem.OpenUpdate(output, [allowed], out var created))
            {
                Assert.False(created);
                Assert.Equal(42, stream.ReadByte());
                stream.WriteByte(43);
            }

            Assert.Equal(new byte[] { 42, 43 }, File.ReadAllBytes(output));
        }
        finally
        {
            File.SetUnixFileMode(restricted, originalMode);
        }
    }

    [UnixFact(Timeout = 5000)]
    public async Task NamedPipeIsRejectedWithoutWaitingForAnotherProcessAsync()
    {
        var path = Path.Combine(this._allowedDirectory, "pipe");
        Assert.Equal(0, MakeFifo(path, 0x180));
        await Task.Run(() =>
        {
            Assert.Throws<InvalidOperationException>(() => SecureFileSystem.OpenRead(path, [this._allowedDirectory], out _));
            Assert.Throws<InvalidOperationException>(() => SecureFileSystem.OpenWrite(path, [this._allowedDirectory], out _));
        });
    }

    [UnixFact]
    public void DeviceIsNotTreatedAsAnOrdinaryFile()
    {
        Assert.Throws<InvalidOperationException>(() => SecureFileSystem.OpenRead("/dev/null", ["/dev"], out _));
        Assert.Throws<InvalidOperationException>(() => SecureFileSystem.OpenWrite("/dev/null", ["/dev"], out _));
    }

    [DllImport("libc", EntryPoint = "mkfifo", SetLastError = true)]
    private static extern int MakeFifo(string path, uint mode);

    public void Dispose()
    {
        try
        {
            Directory.Delete(this._tempDirectory, recursive: true);
        }
        catch (IOException)
        {
        }
        catch (UnauthorizedAccessException)
        {
        }
    }
}
