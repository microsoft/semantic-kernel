using System;
using System.Collections.Generic;
using CommandLine;
using Microsoft.ApplicationInspector.Logging;

namespace Microsoft.DevSkim.CLI.Options;

[Verb("verify", HelpText = "Verify rule validity")]
public record VerifyCommandOptions : LogOptions
{
    [Option('r', HelpText = "Comma separated list of paths to rules files to use", Separator = ',')]
    public IEnumerable<string> Rules { get; set; } = Array.Empty<string>();

    [Option("languages", Required = false, HelpText = "Path to custom json formatted Language file to specify languages, when specified comments must also be specified")]
    public string LanguagesPath { get; set; } = string.Empty;

    [Option("comments", Required = false, HelpText = "Path to custom json formatted Comments file to specify languages, when specified languages must also be specified")]
    public string CommentsPath { get; set; } = string.Empty;
}