using System;
using CommandLine;

namespace Microsoft.DevSkim.CLI.Options;

[Verb("analyze", HelpText = "Analyze source code using DevSkim")]
public record AnalyzeCommandOptions : BaseAnalyzeCommandOptions
{
    [Option("options-json",
        HelpText = "The path to a .json file that contains a serialized SerializedAnalyzeCommandOptions object which can specify both Analyze options and extra options. Options specified explicitly override options from this argument.", Default = "")]
    public string PathToOptionsJson { get; set; } = String.Empty;
}