// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Runtime.InteropServices;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides utility methods for secure path resolution, including symbolic link handling.
/// </summary>
[ExcludeFromCodeCoverage]
internal static class PathUtilities
{
    internal static StringComparison PathComparison { get; } =
        RuntimeInformation.IsOSPlatform(OSPlatform.Windows)
            ? StringComparison.OrdinalIgnoreCase
            : StringComparison.Ordinal;

    /// <summary>
    /// Returns the canonical full path for <paramref name="path"/> with symbolic links handled safely.
    /// On .NET 6 and later, symbolic links are resolved to their final target. On older frameworks,
    /// where links cannot be resolved safely, any path containing a symbolic link is rejected.
    /// </summary>
    /// <param name="path">The path to canonicalize.</param>
    /// <returns>The fully resolved canonical path.</returns>
    /// <exception cref="InvalidOperationException">
    /// On frameworks older than .NET 6, thrown if the path contains a symbolic link.
    /// </exception>
    internal static string GetSafeFullPath(string path)
    {
        var fullPath = Path.GetFullPath(path);

#if NET6_0_OR_GREATER
        return ResolveExistingSegments(fullPath);
#else
        ThrowIfPathContainsReparsePoint(fullPath);
        return fullPath;
#endif
    }

#if NET6_0_OR_GREATER
    private static string ResolveExistingSegments(string fullPath)
    {
        var root = Path.GetPathRoot(fullPath) ?? string.Empty;
        return ResolveSegments(root, GetSegmentsAfterRoot(fullPath, root));
    }

    private static string ResolveSegments(string basePath, string[] segments)
    {
        var resolvedPath = basePath;
        for (var i = 0; i < segments.Length; i++)
        {
            var candidatePath = CombinePath(resolvedPath, segments[i]);

            if (!TryGetFileSystemInfo(candidatePath, out var fileSystemInfo))
            {
                return CombineRemainingPath(candidatePath, segments, i + 1);
            }

            var linkTarget = ResolveLinkTarget(fileSystemInfo);
            if (linkTarget is not null)
            {
                // The link target may itself contain unresolved symbolic links,
                // so canonicalize it before continuing with the remaining segments.
                resolvedPath = ResolveExistingSegments(linkTarget);
            }
            else
            {
                resolvedPath = candidatePath;
            }
        }

        return resolvedPath;
    }

    private static bool TryGetFileSystemInfo(string path, [NotNullWhen(true)] out FileSystemInfo? fileSystemInfo)
    {
        if (!TryGetAttributes(path, out var attributes))
        {
            fileSystemInfo = null;
            return false;
        }

        fileSystemInfo = (attributes & FileAttributes.Directory) != 0
            ? new DirectoryInfo(path)
            : new FileInfo(path);
        return true;
    }

    private static string? ResolveLinkTarget(FileSystemInfo fileSystemInfo)
    {
        if ((fileSystemInfo.Attributes & FileAttributes.ReparsePoint) == 0)
        {
            return null;
        }

        try
        {
            var target = fileSystemInfo.ResolveLinkTarget(returnFinalTarget: true);
            return target?.FullName
                ?? throw new InvalidOperationException(
                    $"Access denied: path contains a symbolic link that cannot be resolved at '{fileSystemInfo.FullName}'.");
        }
        catch (IOException)
        {
            throw new InvalidOperationException(
                $"Access denied: path contains a symbolic link that cannot be resolved at '{fileSystemInfo.FullName}'.");
        }
    }
#endif

#if !NET6_0_OR_GREATER
    private static void ThrowIfPathContainsReparsePoint(string fullPath)
    {
        var root = Path.GetPathRoot(fullPath) ?? string.Empty;
        var segments = GetSegmentsAfterRoot(fullPath, root);

        var currentPath = root;
        foreach (var segment in segments)
        {
            currentPath = CombinePath(currentPath, segment);

            if (TryGetAttributes(currentPath, out var attributes) &&
                (attributes & FileAttributes.ReparsePoint) != 0)
            {
                throw new InvalidOperationException(
                    $"Access denied: path contains a symbolic link at '{currentPath}'.");
            }
        }
    }
#endif

    private static string[] GetSegmentsAfterRoot(string fullPath, string root)
    {
        return fullPath.Substring(root.Length)
            .Split(new[] { Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar },
                   StringSplitOptions.RemoveEmptyEntries);
    }

    private static bool TryGetAttributes(string path, out FileAttributes attributes)
    {
        try
        {
            attributes = File.GetAttributes(path);
            return true;
        }
        catch (FileNotFoundException)
        {
        }
        catch (DirectoryNotFoundException)
        {
        }

        attributes = default;
        return false;
    }

    private static string CombinePath(string basePath, string segment)
    {
        return string.IsNullOrEmpty(basePath) ? segment : Path.Combine(basePath, segment);
    }

    private static string CombineRemainingPath(string basePath, string[] segments, int startIndex)
    {
        var result = basePath;
        for (var i = startIndex; i < segments.Length; i++)
        {
            result = Path.Combine(result, segments[i]);
        }

        return result;
    }
}
