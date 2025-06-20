// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

namespace Utilities;
public static class FileStorageUtilities
{
    // Path used for storing json processes samples in repository
    private static readonly string s_currentSourceDir = Path.Combine(
        Directory.GetCurrentDirectory(), "..", "..", "..");

    public static string GetRepositoryProcessStateFilepath(string relativePath, bool checkFilepathExists = false)
    {
        string fullPath = Path.Combine(s_currentSourceDir, relativePath);
        if (checkFilepathExists && !Directory.Exists(fullPath))
        {
            throw new KernelException($"Path {fullPath} does not exist");
        }

        return fullPath;
    }
}
