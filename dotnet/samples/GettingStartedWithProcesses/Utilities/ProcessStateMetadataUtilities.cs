// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Process.Models;

namespace Utilities;

public static class ProcessStateMetadataUtilities
{
    // Path used for storing json processes samples in repository
    private static readonly string s_currentSourceDir = Path.Combine(
        Directory.GetCurrentDirectory(), "..", "..", "..");

    private static readonly JsonSerializerOptions s_jsonOptions = new()
    {
        WriteIndented = true,
        DefaultIgnoreCondition = System.Text.Json.Serialization.JsonIgnoreCondition.WhenWritingNull
    };

    public static void DumpProcessStateMetadataLocally(KernelProcessStateMetadata processStateInfo, string jsonFilename)
    {
        var filepath = GetRepositoryProcessStateFilepath(jsonFilename);
        StoreProcessStateLocally(processStateInfo, filepath);
    }

    public static KernelProcessStateMetadata? LoadProcessStateMetadata(string jsonRelativePath)
    {
        var filepath = GetRepositoryProcessStateFilepath(jsonRelativePath, checkFilepathExists: true);

        Console.WriteLine($"Loading ProcessStateMetadata from:\n'{Path.GetFullPath(filepath)}'");

        using StreamReader reader = new(filepath);
        var content = reader.ReadToEnd();
        return JsonSerializer.Deserialize<KernelProcessStateMetadata>(content, s_jsonOptions);
    }

    private static string GetRepositoryProcessStateFilepath(string jsonRelativePath, bool checkFilepathExists = false)
    {
        string filepath = Path.Combine(s_currentSourceDir, jsonRelativePath);
        if (checkFilepathExists && !File.Exists(filepath))
        {
            throw new KernelException($"Filepath {filepath} does not exist");
        }

        return filepath;
    }

    /// <summary>
    /// Function that stores the definition of the SK Process State`.<br/>
    /// </summary>
    /// <param name="processStateInfo">Process State to be stored</param>
    /// <param name="fullFilepath">Filepath to store definition of process in json format</param>
    private static void StoreProcessStateLocally(KernelProcessStateMetadata processStateInfo, string fullFilepath)
    {
        if (!(Path.GetDirectoryName(fullFilepath) is string directory && Directory.Exists(directory)))
        {
            throw new KernelException($"Directory for path '{fullFilepath}' does not exist, could not save process {processStateInfo.Name}");
        }

        if (!(Path.GetExtension(fullFilepath) is string extension && !string.IsNullOrEmpty(extension) && extension == ".json"))
        {
            throw new KernelException($"Filepath for process {processStateInfo.Name} does not have .json extension");
        }

        string content = JsonSerializer.Serialize(processStateInfo, s_jsonOptions);
        Console.WriteLine($"Process State: \n{content}");
        Console.WriteLine($"Saving Process State Locally: \n{Path.GetFullPath(fullFilepath)}");
        File.WriteAllText(fullFilepath, content);
    }
}
