// Copyright (c) Microsoft. All rights reserved.
namespace SemanticKernel.Data.Nl2Sql;

using System;
using System.IO;

/// <summary>
/// Utility class to assist in resolving file-system paths.
/// </summary>
internal static class Repo
{
    public static string RootFolder { get; } = GetRoot();

    public static string RootConfigFolder { get; } = $@"{Repo.RootFolder}\samples\data\nl2sql\nl2sql.config";

    private static string GetRoot()
    {
        var current = Environment.CurrentDirectory;

        var folder = new DirectoryInfo(current);

        while (!Directory.Exists(Path.Combine(folder.FullName, ".git")))
        {
            folder =
                folder.Parent ??
                throw new DirectoryNotFoundException($"Unable to locate repo root folder: {current}");
        }

        return folder.FullName;
    }
}
