// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.IO;
using YamlDotNet.Serialization;

namespace Microsoft.SemanticKernel.Experimental.Prompty.Core;

internal class Prompty()
{
    [YamlMember(Alias = "name")]
    public string? Name;

    [YamlMember(Alias = "description")]
    public string? Description;

    [YamlMember(Alias = "version")]
    public string? Version;

    [YamlMember(Alias = "tags")]
    public List<string>? Tags;

    [YamlMember(Alias = "authors")]
    public List<string>? Authors;

    [YamlMember(Alias = "inputs")]
    public Dictionary<string, dynamic>? Inputs;

    [YamlMember(Alias = "outputs")]
    public Dictionary<string, dynamic>? Outputs;

    [YamlMember(Alias = "model")]
    public PromptyModel Model;

    public string? Prompt { get; set; }
    public List<Dictionary<string, string>> Messages { get; set; }

    public string? FilePath;

    // This is called from Execute to load a prompty file from location to create a Prompty object.
    // If sending a Prompty Object, this will not be used in execute.
    public Prompty Load(string promptyFileName, Prompty prompty)
    {
        //Then load settings from prompty file and override if not null
        var promptyFileInfo = new FileInfo(promptyFileName);

        // Get the full path of the prompty file
        prompty.FilePath = promptyFileInfo.FullName;
        var fileContent = File.ReadAllText(prompty.FilePath);
        // parse file in to frontmatter and prompty based on --- delimiter
        var promptyFrontMatterYaml = fileContent.Split(["---"], System.StringSplitOptions.None)[1];
        var promptyContent = fileContent.Split(["---"], System.StringSplitOptions.None)[2];
        // deserialize yaml into prompty object
        prompty = Helpers.ParsePromptyYamlFile(prompty, promptyFrontMatterYaml);
        prompty.Prompt = promptyContent;

        return prompty;
    }
}
