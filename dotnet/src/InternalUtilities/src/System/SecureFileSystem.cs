// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Runtime.InteropServices;
using System.Security;
using Microsoft.Win32.SafeHandles;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Opens local files without separating path validation from file access.
/// The returned stream owns the same handle that was checked, so replacing a
/// validated path with a symbolic link cannot redirect the later read or write.
/// </summary>
/// <remarks>
/// Allowed roots and their configuration must remain under trusted ownership.
/// This prevents link replacement, not changes to mounts, hard links, or the contents of an open file.
/// Linux file inspection requires libc/kernel support for statx; failure never falls back to a path check.
/// </remarks>
[ExcludeFromCodeCoverage]
internal static class SecureFileSystem
{
    internal static FileStream OpenRead(
        string path,
        IEnumerable<string>? allowedDirectories,
        out string resolvedPath,
        bool rejectReadOnly = false,
        FileShare share = FileShare.Read)
    {
        var allowedPath = GetAllowedPath(path, allowedDirectories);
        resolvedPath = allowedPath.ResolvedPath;
        return OpenRestrictedFile(allowedPath, FileMode.Open, FileAccess.Read, share, rejectReadOnly, out _);
    }

    internal static FileStream OpenWrite(
        string path,
        IEnumerable<string>? allowedDirectories,
        out string resolvedPath,
        FileMode mode = FileMode.Create,
        FileShare share = FileShare.Read)
    {
        if (mode is not FileMode.Create and not FileMode.CreateNew)
        {
            throw new ArgumentOutOfRangeException(nameof(mode));
        }

        var allowedPath = GetAllowedPath(path, allowedDirectories);
        resolvedPath = allowedPath.ResolvedPath;
        return OpenRestrictedFile(allowedPath, mode, FileAccess.Write, share, rejectReadOnly: true, out _);
    }

    internal static FileStream OpenUpdate(
        string path,
        IEnumerable<string>? allowedDirectories,
        out bool created)
    {
        var allowedPath = GetAllowedPath(path, allowedDirectories);
        return OpenRestrictedFile(
            allowedPath, FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None, rejectReadOnly: true, out created);
    }

#pragma warning disable CA2000 // The returned FileStream owns the handle; failures dispose it below.
    private static FileStream OpenRestrictedFile(
        AllowedPath allowedPath,
        FileMode mode,
        FileAccess access,
        FileShare share,
        bool rejectReadOnly,
        out bool created)
    {
        SafeFileHandle fileHandle;
        if (RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
        {
            fileHandle = WindowsFileSystem.Open(
                allowedPath.AllowedDirectory, allowedPath.RelativeSegments, mode, access, share, rejectReadOnly, out created);
        }
        else if (RuntimeInformation.IsOSPlatform(OSPlatform.Linux) ||
                 RuntimeInformation.IsOSPlatform(OSPlatform.OSX))
        {
            fileHandle = UnixFileSystem.Open(
                allowedPath.AllowedDirectory, allowedPath.RelativeSegments, mode, access, share, rejectReadOnly, out created);
        }
        else
        {
            throw new PlatformNotSupportedException(
                "Secure local file access is supported only on Windows, Linux, and macOS.");
        }

        FileStream? stream = null;
        try
        {
            stream = new FileStream(fileHandle, access);
            if (mode == FileMode.Create)
            {
                // Do not truncate an existing file until the securely opened handle has passed every check.
                stream.SetLength(0);
            }

            return stream;
        }
        catch
        {
            stream?.Dispose();
            fileHandle.Dispose();
            throw;
        }
    }
#pragma warning restore CA2000

    internal static string NormalizePath(string path, bool expandEnvironmentVariables = false)
    {
        Verify.NotNullOrWhiteSpace(path);
        RejectNetworkOrDevicePath(path);
        var expanded = expandEnvironmentVariables ? Environment.ExpandEnvironmentVariables(path) : path;
        RejectNetworkOrDevicePath(expanded);
        var fullPath = Path.GetFullPath(expanded);
        RejectNetworkOrDevicePath(fullPath);
        return fullPath;
    }

    private static void RejectNetworkOrDevicePath(string path)
    {
        if (path.Length >= 2 && path[0] is '/' or '\\' && path[1] is '/' or '\\')
        {
            throw new ArgumentException("Invalid file path, UNC paths are not supported.", nameof(path));
        }
    }

    private static AllowedPath GetAllowedPath(string path, IEnumerable<string>? allowedDirectories)
    {
        var fullPath = NormalizePath(path);
        if (allowedDirectories is null)
        {
            throw new InvalidOperationException("File access requires allowed directories to be configured.");
        }

        using var enumerator = allowedDirectories.GetEnumerator();
        if (!enumerator.MoveNext())
        {
            throw new InvalidOperationException("File access requires allowed directories to be configured.");
        }

        // Canonicalization identifies the intended location. The native open below still walks
        // every path part without following links because this string can become stale immediately.
        string resolvedPath;
        try
        {
            resolvedPath = PathUtilities.GetSafeFullPath(fullPath);
            RejectNetworkOrDevicePath(resolvedPath);
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or InvalidOperationException or SecurityException)
        {
            throw new InvalidOperationException("The requested file path is not allowed.");
        }

        do
        {
            // Invalid trusted configuration must remain visible, unlike rejected caller paths.
            var resolvedAllowedDirectory = TrimTrailingSeparators(
                PathUtilities.GetSafeFullPath(NormalizePath(enumerator.Current)));
            RejectNetworkOrDevicePath(resolvedAllowedDirectory);
            var separator = Path.DirectorySeparatorChar.ToString();
            var allowedPrefix = resolvedAllowedDirectory.EndsWith(separator, PathUtilities.PathComparison)
                ? resolvedAllowedDirectory
                : resolvedAllowedDirectory + separator;

            if (!resolvedPath.StartsWith(allowedPrefix, PathUtilities.PathComparison))
            {
                continue;
            }

            var relativePath = resolvedPath.Substring(allowedPrefix.Length);
            var relativeSegments = relativePath.Split(
                new[] { Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar },
                StringSplitOptions.RemoveEmptyEntries);

            if (relativeSegments.Length > 0)
            {
                return new AllowedPath(resolvedAllowedDirectory, resolvedPath, relativeSegments);
            }
        }
        while (enumerator.MoveNext());

        throw new InvalidOperationException("The requested file path is not within allowed directories.");
    }

    private static string TrimTrailingSeparators(string path)
    {
        var rootLength = (Path.GetPathRoot(path) ?? string.Empty).Length;
        var length = path.Length;

        while (length > rootLength &&
               (path[length - 1] == Path.DirectorySeparatorChar ||
                path[length - 1] == Path.AltDirectorySeparatorChar))
        {
            length--;
        }

        return length == path.Length ? path : path.Substring(0, length);
    }

    private readonly struct AllowedPath(
        string allowedDirectory,
        string resolvedPath,
        string[] relativeSegments)
    {
        internal string AllowedDirectory { get; } = allowedDirectory;

        internal string ResolvedPath { get; } = resolvedPath;

        internal string[] RelativeSegments { get; } = relativeSegments;
    }

    private static class UnixFileSystem
    {
        private const int ReadOnly = 0;
        private const int WriteOnly = 1;
        private const int ReadWrite = 2;
        private const int LinuxPathOnly = 0x200000;
        private const uint DefaultPermissions = 0x1B6; // 0666, reduced by the process umask.
        private const int AlreadyExists = 17;

#pragma warning disable CA2000 // Ownership of the verified file handle is returned; failed checks dispose it.
        internal static SafeFileHandle Open(
            string allowedDirectory,
            string[] relativeSegments,
            FileMode mode,
            FileAccess access,
            FileShare share,
            bool rejectReadOnly,
            out bool created)
        {
            created = false;
            var directoryFlags = GetDirectoryFlags();
            var currentHandle = OpenPath("/", directoryFlags);

            try
            {
                // Start at the filesystem root and open each directory relative to its parent.
                // This keeps every parent stable even if its name is replaced during the walk.
                foreach (var segment in GetSegmentsAfterRoot(allowedDirectory))
                {
                    var nextHandle = OpenAt(currentHandle, segment, directoryFlags, 0);
                    currentHandle.Dispose();
                    currentHandle = nextHandle;
                }

                for (var i = 0; i < relativeSegments.Length - 1; i++)
                {
                    var nextHandle = OpenAt(currentHandle, relativeSegments[i], directoryFlags, 0);
                    currentHandle.Dispose();
                    currentHandle = nextHandle;
                }

                var name = relativeSegments[relativeSegments.Length - 1];
                var fileFlags = (access == FileAccess.Read ? ReadOnly : access == FileAccess.Write ? WriteOnly : ReadWrite) |
                    GetNoFollowFlag() | GetCloseOnExecFlag() | GetNonBlockingFlag();

                SafeFileHandle handle;
                if (mode == FileMode.OpenOrCreate)
                {
                    // Exclusive creation supplies reliable creation status. A conflicting file is
                    // opened without truncation; if it vanishes again we fail rather than spin.
                    var descriptor = OpenAtNative(currentHandle, name,
                        fileFlags | GetCreateFlag() | GetExclusiveFlag(), DefaultPermissions);
                    if (descriptor >= 0)
                    {
                        handle = new SafeFileHandle(new IntPtr(descriptor), ownsHandle: true);
                        created = true;
                    }
                    else if (Marshal.GetLastWin32Error() == AlreadyExists)
                    {
                        handle = OpenAt(currentHandle, name, fileFlags, 0);
                    }
                    else
                    {
                        return CreateHandle(descriptor, name);
                    }
                }
                else
                {
                    if (mode is FileMode.Create or FileMode.CreateNew)
                    {
                        fileFlags |= GetCreateFlag();
                    }

                    if (mode == FileMode.CreateNew)
                    {
                        fileFlags |= GetExclusiveFlag();
                    }

                    handle = OpenAt(currentHandle, name, fileFlags, DefaultPermissions);
                    created = mode == FileMode.CreateNew;
                }

                try
                {
                    // Nonblocking open prevents a substituted pipe from hanging before we can
                    // inspect the handle. Only ordinary files may reach the returned FileStream.
                    CheckFile(handle, rejectReadOnly);
                    if (Flock(handle, (share == FileShare.None ? 2 : 1) | 4) != 0)
                    {
                        throw new IOException("The file is in use.");
                    }

                    return handle;
                }
                catch
                {
                    handle.Dispose();
                    throw;
                }
            }
            finally
            {
                currentHandle.Dispose();
            }
        }
#pragma warning restore CA2000

        private static int GetDirectoryFlags() =>
            // Traversal needs search permission, not permission to list each ancestor.
            (RuntimeInformation.IsOSPlatform(OSPlatform.Linux) ? LinuxPathOnly : ReadOnly) |
            GetDirectoryFlag() | GetNoFollowFlag() | GetCloseOnExecFlag();

        private static int GetDirectoryFlag() =>
            RuntimeInformation.IsOSPlatform(OSPlatform.OSX) ? 0x100000 : 0x10000;

        private static int GetCreateFlag() =>
            RuntimeInformation.IsOSPlatform(OSPlatform.OSX) ? 0x200 : 0x40;

        private static int GetExclusiveFlag() =>
            RuntimeInformation.IsOSPlatform(OSPlatform.OSX) ? 0x800 : 0x80;

        private static int GetNonBlockingFlag() =>
            RuntimeInformation.IsOSPlatform(OSPlatform.OSX) ? 0x4 : 0x800;

        private static int GetNoFollowFlag() =>
            RuntimeInformation.IsOSPlatform(OSPlatform.OSX) ? 0x100 : 0x20000;

        private static int GetCloseOnExecFlag() =>
            RuntimeInformation.IsOSPlatform(OSPlatform.OSX) ? 0x1000000 : 0x80000;

        private static string[] GetSegmentsAfterRoot(string path)
        {
            var root = Path.GetPathRoot(path) ?? string.Empty;
            return path.Substring(root.Length).Split(
                new[] { Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar },
                StringSplitOptions.RemoveEmptyEntries);
        }

        private static SafeFileHandle OpenPath(string path, int flags)
        {
            var descriptor = OpenNative(path, flags);
            return CreateHandle(descriptor, path);
        }

        private static SafeFileHandle OpenAt(SafeFileHandle directory, string path, int flags, uint mode)
        {
            var descriptor = OpenAtNative(directory, path, flags, mode);
            return CreateHandle(descriptor, path);
        }

        private static int OpenAtNative(SafeFileHandle directory, string path, int flags, uint mode)
        {
            if (RuntimeInformation.IsOSPlatform(OSPlatform.OSX) &&
                RuntimeInformation.ProcessArchitecture == Architecture.Arm64)
            {
                // Apple's ARM64 openat reads its optional permissions argument from the stack,
                // not a register. Fill the five remaining argument registers so this fixed
                // P/Invoke signature puts mode on the stack, where the native function expects it.
                return OpenAtMacArm64(directory, path, flags,
                    IntPtr.Zero, IntPtr.Zero, IntPtr.Zero, IntPtr.Zero, IntPtr.Zero, mode);
            }

            return OpenAtDefault(directory, path, flags, mode);
        }

        private static void CheckFile(SafeFileHandle handle, bool rejectReadOnly)
        {
            ushort mode;
            if (RuntimeInformation.IsOSPlatform(OSPlatform.Linux))
            {
                // statx has the same layout on all Linux architectures, unlike struct stat.
                if (StatX(handle, string.Empty, 0x1000, 0x3, out var information) != 0)
                {
                    throw new IOException($"Could not inspect the open file. Native error: {Marshal.GetLastWin32Error()}.");
                }

                if ((information.Mask & 0x3) != 0x3)
                {
                    throw new IOException("The filesystem did not supply the file type and permissions.");
                }

                mode = information.Mode;
            }
            else
            {
                var result = RuntimeInformation.ProcessArchitecture == Architecture.X64
                    ? StatMacX64(handle, out var information)
                    : StatMac(handle, out information);
                if (result != 0)
                {
                    throw new IOException($"Could not inspect the open file. Native error: {Marshal.GetLastWin32Error()}.");
                }

                mode = information.Mode;
            }

            if ((mode & 0xF000) != 0x8000)
            {
                throw new InvalidOperationException("Access denied: the target is not a regular file.");
            }

            if (rejectReadOnly && (mode & 0x92) == 0) // No owner, group, or other write permission.
            {
                throw new UnauthorizedAccessException("File is read-only.");
            }
        }

        private static SafeFileHandle CreateHandle(int descriptor, string path)
        {
            if (descriptor < 0)
            {
                var error = Marshal.GetLastWin32Error();
                if (error == 2)
                {
                    throw new FileNotFoundException($"Could not securely open '{path}'.", path);
                }

                if (error == AlreadyExists)
                {
                    throw new FileAlreadyExistsException();
                }

                if (error is 1 or 13 or 30)
                {
                    throw new UnauthorizedAccessException("Access to the file was denied.");
                }

                throw new InvalidOperationException(
                    $"Access denied: '{path}' could not be opened safely. Native error: {error}.");
            }

            return new SafeFileHandle(new IntPtr(descriptor), ownsHandle: true);
        }

        [DllImport("libc", EntryPoint = "open", SetLastError = true)]
        private static extern int OpenNative(string path, int flags);

        [DllImport("libc", EntryPoint = "openat", SetLastError = true)]
        private static extern int OpenAtDefault(SafeFileHandle directoryDescriptor, string path, int flags, uint mode);

        [DllImport("libc", EntryPoint = "openat", SetLastError = true)]
        private static extern int OpenAtMacArm64(
            SafeFileHandle directoryDescriptor, string path, int flags,
            IntPtr unused3, IntPtr unused4, IntPtr unused5, IntPtr unused6, IntPtr unused7, uint mode);

        [DllImport("libc", EntryPoint = "flock", SetLastError = true)]
        private static extern int Flock(SafeFileHandle descriptor, int operation);

        [DllImport("libc", EntryPoint = "statx", SetLastError = true)]
        private static extern int StatX(SafeFileHandle descriptor, string path, int flags, uint mask, out LinuxStatX information);

        [DllImport("libc", EntryPoint = "fstat", SetLastError = true)]
        private static extern int StatMac(SafeFileHandle descriptor, out MacStat information);

        [DllImport("libc", EntryPoint = "fstat$INODE64", SetLastError = true)]
        private static extern int StatMacX64(SafeFileHandle descriptor, out MacStat information);

        [StructLayout(LayoutKind.Explicit, Size = 256)]
        private struct LinuxStatX
        {
            [FieldOffset(0)]
            internal uint Mask;
            [FieldOffset(28)]
            internal ushort Mode;
        }

        [StructLayout(LayoutKind.Explicit, Size = 144)]
        private struct MacStat
        {
            [FieldOffset(4)]
            internal ushort Mode;
        }
    }

#pragma warning disable RCS1194 // Internal marker for the atomic create-only conflict, with a fixed message.
    internal sealed class FileAlreadyExistsException : IOException
    {
        internal FileAlreadyExistsException() : base("Overwriting existing files is disabled.")
        {
        }
    }
#pragma warning restore RCS1194

    private static class WindowsFileSystem
    {
        private const uint GenericRead = 0x80000000;
        private const uint GenericWrite = 0x40000000;
        private const uint FileListDirectory = 0x00000001;
        private const uint FileReadAttributes = 0x00000080;
        private const uint Synchronize = 0x00100000;
        private const uint FileShareRead = 0x00000001;
        private const uint FileShareWrite = 0x00000002;
        private const uint FileShareDelete = 0x00000004;
        private const uint OpenExisting = 3;
        private const uint FileOpen = 1;
        private const uint FileCreate = 2;
        private const uint FileOpenIf = 3;
        private const uint FileAttributeNormal = 0x00000080;
        private const uint FileAttributeReparsePoint = 0x00000400;
        private const uint FileFlagBackupSemantics = 0x02000000;
        private const uint FileFlagOpenReparsePoint = 0x00200000;
        private const uint FileDirectoryFile = 0x00000001;
        private const uint FileSynchronousIoNonAlert = 0x00000020;
        private const uint FileNonDirectoryFile = 0x00000040;
        private const uint ObjectCaseInsensitive = 0x00000040;
        private const int StatusObjectNameNotFound = unchecked((int)0xC0000034);
        private const int StatusObjectPathNotFound = unchecked((int)0xC000003A);
        private const int StatusObjectNameCollision = unchecked((int)0xC0000035);
        private const int StatusAccessDenied = unchecked((int)0xC0000022);

        internal static SafeFileHandle Open(
            string allowedDirectory,
            string[] relativeSegments,
            FileMode mode,
            FileAccess access,
            FileShare share,
            bool rejectReadOnly,
            out bool created)
        {
            var rootPath = Path.GetPathRoot(allowedDirectory)
                ?? throw new InvalidOperationException($"Access denied: '{allowedDirectory}' has no path root.");

            var currentHandle = OpenRoot(rootPath);

            try
            {
                // Handle-relative opens prevent a checked parent directory from being swapped
                // before the next path part is opened.
                foreach (var segment in GetSegmentsAfterRoot(allowedDirectory, rootPath))
                {
                    var nextHandle = OpenRelativeDirectory(currentHandle, segment);
                    currentHandle.Dispose();
                    currentHandle = nextHandle;
                }

                for (var i = 0; i < relativeSegments.Length - 1; i++)
                {
                    var nextHandle = OpenRelativeDirectory(currentHandle, relativeSegments[i]);
                    currentHandle.Dispose();
                    currentHandle = nextHandle;
                }

                return OpenRelativeFile(
                    currentHandle,
                    relativeSegments[relativeSegments.Length - 1],
                    mode, access, share, rejectReadOnly, out created);
            }
            finally
            {
                currentHandle.Dispose();
            }
        }

        private static SafeFileHandle OpenRoot(string rootPath)
        {
            var handle = CreateFile(
                rootPath,
                FileListDirectory | FileReadAttributes | Synchronize,
                FileShareRead | FileShareWrite | FileShareDelete,
                IntPtr.Zero,
                OpenExisting,
                FileFlagBackupSemantics | FileFlagOpenReparsePoint,
                IntPtr.Zero);

            if (handle.IsInvalid)
            {
                var error = Marshal.GetLastWin32Error();
                handle.Dispose();
                throw new InvalidOperationException(
                    $"Access denied: path root '{rootPath}' could not be opened safely. Native error: {error}.");
            }

            ThrowIfReparsePoint(handle, rootPath);
            return handle;
        }

        private static SafeFileHandle OpenRelativeDirectory(SafeFileHandle parent, string segment)
        {
            var handle = OpenRelative(
                parent,
                segment,
                FileListDirectory | FileReadAttributes | Synchronize,
                FileOpen,
                FileDirectoryFile | FileSynchronousIoNonAlert,
                FileShareRead,
                out _);

            ThrowIfReparsePoint(handle, segment);
            return handle;
        }

        private static SafeFileHandle OpenRelativeFile(
            SafeFileHandle parent,
            string segment,
            FileMode mode,
            FileAccess access,
            FileShare share,
            bool rejectReadOnly,
            out bool created)
        {
            var desiredAccess = (access == FileAccess.Read ? GenericRead :
                access == FileAccess.Write ? GenericWrite : GenericRead | GenericWrite) |
                FileReadAttributes |
                Synchronize;
            var disposition = mode == FileMode.Open ? FileOpen :
                mode == FileMode.CreateNew ? FileCreate : FileOpenIf;

            var handle = OpenRelative(
                parent,
                segment,
                desiredAccess,
                disposition,
                FileNonDirectoryFile | FileSynchronousIoNonAlert,
                (uint)share,
                out created);

            // Opening the reparse point itself lets us reject it before any file content is changed.
            try
            {
                var attributes = ThrowIfReparsePoint(handle, segment);
                if (GetFileType(handle) != 1 || (attributes & 0x10) != 0)
                {
                    throw new InvalidOperationException("Access denied: the target is not a regular file.");
                }

                if (rejectReadOnly && (attributes & 1) != 0)
                {
                    throw new UnauthorizedAccessException("File is read-only.");
                }

                return handle;
            }
            catch
            {
                handle.Dispose();
                throw;
            }
        }

        private static SafeFileHandle OpenRelative(
            SafeFileHandle parent,
            string segment,
            uint desiredAccess,
            uint disposition,
            uint options,
            uint share,
            out bool created)
        {
            var stringBuffer = Marshal.StringToHGlobalUni(segment);
            var unicodeStringPointer = IntPtr.Zero;

            try
            {
                var unicodeString = new UnicodeString
                {
                    Length = checked((ushort)(segment.Length * sizeof(char))),
                    MaximumLength = checked((ushort)((segment.Length + 1) * sizeof(char))),
                    Buffer = stringBuffer,
                };

                unicodeStringPointer = Marshal.AllocHGlobal(Marshal.SizeOf<UnicodeString>());
                Marshal.StructureToPtr(unicodeString, unicodeStringPointer, fDeleteOld: false);

                var objectAttributes = new ObjectAttributes
                {
                    Length = Marshal.SizeOf<ObjectAttributes>(),
                    RootDirectory = parent.DangerousGetHandle(),
                    ObjectName = unicodeStringPointer,
                    Attributes = ObjectCaseInsensitive,
                };

                var status = NtCreateFile(
                    out var rawHandle,
                    desiredAccess,
                    ref objectAttributes,
                    out var ioStatus,
                    IntPtr.Zero,
                    FileAttributeNormal,
                    share,
                    disposition,
                    options | FileFlagOpenReparsePoint,
                    IntPtr.Zero,
                    0);

                if (status < 0)
                {
                    if (status == StatusObjectNameCollision)
                    {
                        throw new FileAlreadyExistsException();
                    }

                    if (status == StatusAccessDenied)
                    {
                        throw new UnauthorizedAccessException("Access to the file was denied.");
                    }

                    if (status == StatusObjectNameNotFound || status == StatusObjectPathNotFound)
                    {
                        throw new FileNotFoundException($"Could not securely open '{segment}'.", segment);
                    }

                    throw new InvalidOperationException(
                        $"Access denied: '{segment}' could not be opened safely. NTSTATUS: 0x{status:X8}.");
                }

                created = ioStatus.Information == new IntPtr(2);
                return new SafeFileHandle(rawHandle, ownsHandle: true);
            }
            finally
            {
                if (unicodeStringPointer != IntPtr.Zero)
                {
                    Marshal.FreeHGlobal(unicodeStringPointer);
                }

                Marshal.FreeHGlobal(stringBuffer);
            }
        }

        private static uint ThrowIfReparsePoint(SafeFileHandle handle, string segment)
        {
            if (!GetFileInformationByHandle(handle, out var information))
            {
                var error = Marshal.GetLastWin32Error();
                handle.Dispose();
                throw new InvalidOperationException(
                    $"Access denied: '{segment}' could not be inspected safely. Native error: {error}.");
            }

            if ((information.FileAttributes & FileAttributeReparsePoint) != 0)
            {
                handle.Dispose();
                throw new InvalidOperationException(
                    $"Access denied: path contains a symbolic link or reparse point at '{segment}'.");
            }

            return information.FileAttributes;
        }

        private static string[] GetSegmentsAfterRoot(string path, string root) =>
            path.Substring(root.Length).Split(
                new[] { Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar },
                StringSplitOptions.RemoveEmptyEntries);

        [StructLayout(LayoutKind.Sequential)]
        private struct UnicodeString
        {
            internal ushort Length;
            internal ushort MaximumLength;
            internal IntPtr Buffer;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct ObjectAttributes
        {
            internal int Length;
            internal IntPtr RootDirectory;
            internal IntPtr ObjectName;
            internal uint Attributes;
            internal IntPtr SecurityDescriptor;
            internal IntPtr SecurityQualityOfService;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct IoStatusBlock
        {
            internal IntPtr Status;
            internal IntPtr Information;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct ByHandleFileInformation
        {
            internal uint FileAttributes;
            internal System.Runtime.InteropServices.ComTypes.FILETIME CreationTime;
            internal System.Runtime.InteropServices.ComTypes.FILETIME LastAccessTime;
            internal System.Runtime.InteropServices.ComTypes.FILETIME LastWriteTime;
            internal uint VolumeSerialNumber;
            internal uint FileSizeHigh;
            internal uint FileSizeLow;
            internal uint NumberOfLinks;
            internal uint FileIndexHigh;
            internal uint FileIndexLow;
        }

        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        private static extern SafeFileHandle CreateFile(
            string fileName,
            uint desiredAccess,
            uint shareMode,
            IntPtr securityAttributes,
            uint creationDisposition,
            uint flagsAndAttributes,
            IntPtr templateFile);

        [DllImport("kernel32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool GetFileInformationByHandle(
            SafeFileHandle file,
            out ByHandleFileInformation fileInformation);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern uint GetFileType(SafeFileHandle file);

        [DllImport("ntdll.dll")]
        private static extern int NtCreateFile(
            out IntPtr fileHandle,
            uint desiredAccess,
            ref ObjectAttributes objectAttributes,
            out IoStatusBlock ioStatusBlock,
            IntPtr allocationSize,
            uint fileAttributes,
            uint shareAccess,
            uint createDisposition,
            uint createOptions,
            IntPtr eaBuffer,
            uint eaLength);
    }
}
