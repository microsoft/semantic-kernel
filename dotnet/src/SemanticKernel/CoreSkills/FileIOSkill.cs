// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.CoreSkills;

/// <summary>
/// Read and write from a file.
/// </summary>
/// <example>
/// Usage: kernel.ImportSkill("file", new FileIOSkill());
/// Examples:
/// {{file.readAsync $path }} => "hello world"
/// {{file.writeAsync}}
/// </example>
public class FileIOSkill
{
    /// <summary>
    /// Read a file
    /// </summary>
    /// <example>
    /// {{file.readAsync $path }} => "hello world"
    /// </example>
    /// <param name="path"> Source file </param>
    /// <returns> File content </returns>
    [SKFunction("Read a file")]
    [SKFunctionInput(Description = "Source file")]
    public Task<string?> ReadAsync(string path)
    {
        return Task.FromResult(File.ReadAllText(path));
    }

    /// <summary>
    /// Write a file
    /// </summary>
    /// <example>
    /// {{file.writeAsync}}
    /// </example>
    /// <param name="context">
    /// Contains the 'path' for the Destination file and 'content' of the file to write.
    /// </param>
    /// <returns> An awaitable task </returns>
    [SKFunction("Write a file")]
    [SKFunctionContextParameter(Name = "path", Description = "Destination file")]
    [SKFunctionContextParameter(Name = "content", Description = "File content")]
    public Task WriteAsync(SKContext context)
    {
        File.WriteAllText(context["path"], context["content"]);

        return Task.CompletedTask;
    }
}
