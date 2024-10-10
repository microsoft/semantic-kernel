using System;
using System.Collections.Generic;
using CommandLine;
using Microsoft.ApplicationInspector.Logging;

namespace Microsoft.DevSkim.CLI.Options;

[Verb("suppress", HelpText = "Suppress issues identified in a DevSkim Sarif")]
public record SuppressionCommandOptions : LogOptions
{
    [Option('I', "source-code", Required = true, HelpText = "Path to the parent directory containing the source code that was scanned to produce the sarif.")]
    public string Path { get; set; } = String.Empty;
    [Option('O', "sarif-result", Required = true, HelpText = "Filename for the output sarif from DevSkim Analyze.")]
    public string SarifInput { get; set; } = String.Empty;
    [Option("dry-run", HelpText = "Print information about files that would be changed without changing them.")]
    public bool DryRun { get; set; }
    [Option("all", HelpText = "Apply all ignore.")]
    public bool ApplyAllSuppression { get; set; }
    [Option("files", HelpText = "Comma separated list of paths to apply ignore to", Separator = ',')]
    public IEnumerable<string> FilesToApplyTo { get; set; } = Array.Empty<string>();
    [Option("rules", HelpText = "Comma separated list of rules to apply ignore for", Separator = ',')]
    public IEnumerable<string> RulesToApplyFrom { get; set; } = Array.Empty<string>();

    [Option("prefer-multiline", HelpText = "Prefer using multi-line formatted suppression comments", Default = false)]
    public bool PreferMultiline { get; set; }

    [Option("duration", HelpText = "Optional duration for suppressions in days from current system time", Default = 0)]
    public int Duration { get; set; } = 0;

    [Option("languages", Required = false, HelpText = "Path to custom json formatted Language file to specify languages, when specified comments must also be specified")]
    public string LanguagesPath { get; set; } = string.Empty;

    [Option("comments", Required = false, HelpText = "Path to custom json formatted Comments file to specify languages, when specified languages must also be specified")]
    public string CommentsPath { get; set; } = string.Empty;

    [Option("reviewer", Required = false,
        HelpText = "Set an optional reviewer name to be associated with added suppressions")]
    public string Reviewer { get; set; } = string.Empty;
}