// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.IO;
using Prompty.Core.Types;
using YamlDotNet.Serialization;

namespace Prompty.Core;

public class Prompty()
{
    // PromptyModelConfig model, string prompt, bool isFromSettings = true
    // TODO: validate  the prompty attributes needed, what did I miss that should be included?
    [YamlMember(Alias = "name")]
    public string? Name;

    [YamlMember(Alias = "description")]
    public string? Description;

    [YamlMember(Alias = "tags")]
    public List<string>? Tags;

    [YamlMember(Alias = "authors")]
    public List<string>? Authors;

    [YamlMember(Alias = "inputs")]
    public Dictionary<string, dynamic> Inputs;

    [YamlMember(Alias = "parameters")]
    public Dictionary<string, dynamic> Parameters;

    [YamlMember(Alias = "model")]
    public PromptyModelConfig Model;

    [YamlMember(Alias = "api")]
    public ApiType? modelApiType;

    public string? Prompt { get; set; }
    public List<Dictionary<string, string>> Messages { get; set; }

    public string FilePath;

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
