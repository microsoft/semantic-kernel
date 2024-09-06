using System;
using System.Collections.Generic;
using CommandLine;
using Microsoft.ApplicationInspector.Logging;

namespace Microsoft.DevSkim.CLI.Options;

[Verb("fix", HelpText = "Apply fixes from a Sarif")]
public record FixCommandOptions : LogOptions
{
    [Option('I', "source-code", Required = true, HelpText = "Path to the parent directory containing the source code that was scanned to produce the sarif.")]
    public string Path { get; set; } = String.Empty;

    [Option('O', "sarif-result", Required = true, HelpText = "Filename for the output sarif from DevSkim Analyze.")]
    public string SarifInput { get; set; } = String.Empty;

    [Option("dry-run", HelpText = "Print information about files that would be changed without changing them.")]
    public bool DryRun { get; set; }

    [Option("all", HelpText = "Apply all fixes.")]
    public bool ApplyAllFixes { get; set; }

    [Option("files", HelpText = "Comma separated list of paths to apply fixes to", Separator = ',')]
    public IEnumerable<string> FilesToApplyTo { get; set; } = Array.Empty<string>();

    [Option("rules", HelpText = "Comma separated list of rules to apply fixes for", Separator = ',')]
    public IEnumerable<string> RulesToApplyFrom { get; set; } = Array.Empty<string>();
}