using System;
using System.Collections.Generic;
using CommandLine;
using Microsoft.ApplicationInspector.Logging;
using Microsoft.ApplicationInspector.RulesEngine;
using Microsoft.DevSkim.CLI.Writers;

namespace Microsoft.DevSkim.CLI.Options;

public record BaseAnalyzeCommandOptions : LogOptions
{
    [Option('I', "source-code", Required = true, HelpText = "Path to a directory containing files to scan or a single file to scan", Default = "")]
    public string Path { get; set; } = string.Empty;

    [Option('O', "output-file", Required = false, HelpText = "Filename for result file, uses stdout if not set.", Default = "")]
    public string OutputFile { get; set; } = string.Empty;

    [Option('r', HelpText = "Comma separated list of paths to rules files to use", Separator = ',', Default = new string[] { })]
    public IEnumerable<string> Rules { get; set; } = Array.Empty<string>();

    [Option("rule-ids", HelpText = "Comma separated list of rule IDs to limit analysis to", Separator = ',', Default = new string[] { })]
    public IEnumerable<string> RuleIds { get; set; } = Array.Empty<string>();

    [Option("ignore-rule-ids", HelpText = "Comma separated list of rule IDs to ignore", Separator = ',', Default = new string[] { })]
    public IEnumerable<string> IgnoreRuleIds { get; set; } = Array.Empty<string>();

    [Option("languages", HelpText = "Path to custom json formatted Language file to specify languages, when specified comments must also be specified", Default = "")]
    public string LanguagesPath { get; set; } = string.Empty;

    [Option("comments", Required = false, HelpText = "Path to custom json formatted Comments file to specify languages, when specified languages must also be specified", Default = "")]
    public string CommentsPath { get; set; } = string.Empty;

    [Option('o', "output-format", HelpText = "Format for output text.", Default = SimpleTextWriter.DefaultFormat)]
    public string OutputTextFormat { get; set; } = SimpleTextWriter.DefaultFormat;

    [Option('f', "file-format", HelpText = "Format type for output. [text|sarif]", Default = "sarif")]
    public string OutputFileFormat { get; set; } = "sarif";

    [Option('s', "severity", HelpText = "Comma-separated Severities to match", Separator = ',', Default = new[] { Severity.Critical, Severity.Important, Severity.Moderate, Severity.BestPractice, Severity.ManualReview })]
    public IEnumerable<Severity> Severities { get; set; } = new[] { Severity.Critical, Severity.Important, Severity.Moderate, Severity.BestPractice, Severity.ManualReview };

    [Option("confidence", HelpText = "Comma-separated Severities to match", Separator = ',', Default = new[] { Confidence.High, Confidence.Medium })]
    public IEnumerable<Confidence> Confidences { get; set; } = new[] { Confidence.High, Confidence.Medium };

    [Option('g', "ignore-globs", HelpText = "Comma-separated Globs for files to skip analyzing", Separator = ',', Default = new[] { "**/.git/**", "**/bin/**" })]
    public IEnumerable<string> Globs { get; set; } = new[] { "**/.git/**", "**/bin/**" };

    [Option('d', "disable-supression", HelpText = "Disable comment suppressions", Default = false)]
    public bool DisableSuppression { get; set; }

    [Option("disable-parallel", HelpText = "Disable parallel processing", Default = false)]
    public bool DisableParallel { get; set; }

    [Option('i', "ignore-default-rules", HelpText = "Ignore default rules", Default = false)]
    public bool IgnoreDefaultRules { get; set; }

    [Option('c', "crawl-archives", HelpText = "Analyze files contained inside of archives", Default = false)]
    public bool CrawlArchives { get; set; }

    [Option('E', HelpText = "Use exit code for number of issues. Negative on error.", Default = false)]
    public bool ExitCodeIsNumIssues { get; set; }

    [Option("base-path",
        HelpText =
            "Specify what path to root result URIs in Sarif results with. When not set will generate paths relative to the source directory (or directory containing the source file specified)", Default = "")]
    public string BasePath { get; set; } = string.Empty;

    [Option("absolute-path", HelpText = "Output absolute paths (overrides --base-path).", Default = false)]
    public bool AbsolutePaths { get; set; }

    [Option("skip-git-ignored-files", HelpText = "Set to skip files which are ignored by .gitignore. Requires git to be installed.", Default = false)]
    public bool RespectGitIgnore { get; set; }

    [Option("skip-excerpts", HelpText = "Set to skip gathering excerpts and samples to include in the report.", Default = false)]
    public bool SkipExcerpts { get; set; }
}