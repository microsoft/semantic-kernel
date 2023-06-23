// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.IO;
using System.Text;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Skills.Core;

/// <summary>
/// Read and write from a file.
/// </summary>
/// <example>
/// Usage: kernel.ImportSkill("file", new FileIOSkill());
/// Examples:
/// {{file.readAsync $path }} => "hello world"
/// {{file.writeAsync}}
/// </example>
public sealed class FileIOSkill
{
    /// <summary>
    /// Read a file
    /// </summary>
    /// <example>
    /// {{file.readAsync $path }} => "hello world"
    /// </example>
    /// <param name="path"> Source file </param>
    /// <returns> File content </returns>
    [SKFunction, Description("Read a file")]
    public async Task<string> ReadAsync([Description("Source file")] string path)
    {
        using var reader = File.OpenText(path);
        return await reader.ReadToEndAsync().ConfigureAwait(false);
    }

    /// <summary>
    /// Write a file
    /// </summary>
    /// <example>
    /// {{file.writeAsync}}
    /// </example>
    /// <param name="path">The destination file path</param>
    /// <param name="content">The file content to write</param>
    /// <returns> An awaitable task </returns>
    [SKFunction, Description("Write a file")]
    public async Task WriteAsync(
        [Description("Destination file")] string path,
        [Description("File content")] string content)
    {
        byte[] text = Encoding.UTF8.GetBytes(content);
        if (File.Exists(path) && File.GetAttributes(path).HasFlag(FileAttributes.ReadOnly))
        {
            // Most environments will throw this with OpenWrite, but running inside docker on Linux will not.
            throw new UnauthorizedAccessException($"File is read-only: {path}");
        }

        using var writer = File.OpenWrite(path);
        await writer.WriteAsync(text, 0, text.Length).ConfigureAwait(false);
    }
}
