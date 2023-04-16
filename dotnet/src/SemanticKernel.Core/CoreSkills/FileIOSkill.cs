// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Text;
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
    public async Task<string> ReadAsync(string path)
    {
        using var reader = File.OpenText(path);
        return await reader.ReadToEndAsync();
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
    public async Task WriteAsync(SKContext context)
    {
        byte[] text = Encoding.UTF8.GetBytes(context["content"]);
        using var writer = File.OpenWrite(context["path"]);
        await writer.WriteAsync(text, 0, text.Length);
    }
}
