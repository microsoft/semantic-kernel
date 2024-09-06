using System;
using Microsoft.CodeAnalysis.Sarif;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Runtime.InteropServices;
using Microsoft.ApplicationInspector.RulesEngine;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace Microsoft.DevSkim.CLI.Writers
{
    public class SarifWriter : Writer
    {
        public SarifWriter(TextWriter writer, string? outputPath, GitInformation? gitInformation)
        {
            _gitInformation = gitInformation;
            TextWriter = writer;
            OutputPath = outputPath;
        }

        public override void FlushAndClose()
        {
            SarifLog sarifLog = new SarifLog
            {
                Version = SarifVersion.Current
            };
            Run runItem = new Run
            {
                Tool = new Tool
                {
                    Driver = new ToolComponent()
                    {
                        Rules = _rules.Select(x => x.Value).ToList(),
                        InformationUri = new Uri("https://github.com/microsoft/DevSkim/")
                    }
                },
                Results = _results.ToList()
            };

            if (Assembly.GetEntryAssembly() is { } entryAssembly)
            {
                runItem.Tool.Driver.Name = entryAssembly.GetName().Name;

                runItem.Tool.Driver.FullName = entryAssembly.GetCustomAttribute<AssemblyProductAttribute>()?
                    .Product;

                runItem.Tool.Driver.Version = entryAssembly.GetCustomAttribute<AssemblyInformationalVersionAttribute>()?
                    .InformationalVersion;
            }

            if (_gitInformation is not null)
            {
                runItem.VersionControlProvenance = new List<VersionControlDetails>()
                {
                    new()
                    {
                        Branch = _gitInformation.Branch,
                        RepositoryUri = _gitInformation.RepositoryUri,
                        RevisionId = _gitInformation.CommitHash
                    }
                };
            }

            sarifLog.Runs = new List<Run>();
            sarifLog.Runs.Add(runItem);

            // Begin Workaround for https://github.com/microsoft/sarif-sdk/issues/2024

            // Save the sarif log to a stream
            var stream = new MemoryStream();
            sarifLog.Save(stream);
            stream.Position = 0;
            // Read the saved log back in
            var reReadLog = JObject.Parse(new StreamReader(stream).ReadToEnd());
            // Find results with levels that are not set
            var resultsWithoutLevels =
                reReadLog.SelectTokens("$.runs[*].results[*]").Where(t => t["level"] == null).ToList();
            // For each result with no level set its level to warning
            foreach (var result in resultsWithoutLevels)
            {
                result["level"] = "warning";
            }

            // Rules which had a default configuration of Warning will also not have the field populated
            var rulesWithoutDefaultConfiguration = reReadLog.SelectTokens("$.runs[*].tool.driver.rules[*]")
                .Where(t => t["defaultConfiguration"] == null).ToList();
            // For each result with no default configuration option, add one with the level warning
            foreach (var rule in rulesWithoutDefaultConfiguration)
            {
                rule["defaultConfiguration"] = new JObject { { "level", "warning" } };
            }

            // Rules with a DefaultConfiguration object, but where that object has no level also should be set
            //  DevSkim should always populate this object with a level, but potentially
            var rulesWithoutDefaultConfigurationLevel = reReadLog.SelectTokens("$.runs[*].tool.driver.rules[*].defaultConfiguration")
                .Where(t => t["level"] == null).ToList();
            // For each result with a default configuration object that has no level
            //  add a level property equal to warning
            foreach (var rule in rulesWithoutDefaultConfigurationLevel)
            {
                rule["level"] = "warning";
            }

            // Write out the fixed sarif
            using var jsonWriter = new JsonTextWriter(TextWriter);
            reReadLog.WriteTo(jsonWriter);
            // Add a newline at the end to make logging messages cleaner
            TextWriter.WriteLine();

            // End Workarounds
            TextWriter.Flush();
        }

        private ConcurrentDictionary<string, ArtifactLocation> locationCache = new ConcurrentDictionary<string, ArtifactLocation>();

        private ArtifactLocation GetValueAndImplicitlyPopulateCache(string path)
        {
            if (locationCache.TryGetValue(path, out ArtifactLocation? value))
            {
                return value;
            }

            // Need to add UriBaseId = "%srcroot%" when not using absolute paths
            ArtifactLocation newVal = new ArtifactLocation() { Uri = new Uri(path, UriKind.Relative) };
            locationCache[path] = newVal;
            return newVal;
        }

        public override void WriteIssue(IssueRecord issue)
        {
            Result resultItem = new Result();
            MapRuleToResult(issue.Issue.Rule, ref resultItem);
            AddRuleToSarifRule(issue.Issue.Rule);

            CodeAnalysis.Sarif.Location loc = new CodeAnalysis.Sarif.Location()
            {
                PhysicalLocation = new PhysicalLocation()
                {
                    ArtifactLocation = GetValueAndImplicitlyPopulateCache(issue.Filename),
                    Region = new Region()
                    {
                        StartColumn = issue.Issue.StartLocation.Column,
                        StartLine = issue.Issue.StartLocation.Line,
                        EndColumn = issue.Issue.EndLocation.Column,
                        EndLine = issue.Issue.EndLocation.Line,
                        CharOffset = issue.Issue.Boundary.Index,
                        CharLength = issue.Issue.Boundary.Length,
                        Snippet = new ArtifactContent()
                        {
                            Text = issue.TextSample,
                            Rendered = new MultiformatMessageString(issue.TextSample, $"`{issue.TextSample}`", null),
                        },
                        SourceLanguage = issue.Language
                    }
                }
            };

            if (issue.Issue.Rule.Fixes != null)
            {
                resultItem.Fixes = GetFixits(issue);
            }

            resultItem.Level = DevSkimLevelToSarifLevel(issue.Issue.Rule.Severity);
            resultItem.Locations = new List<CodeAnalysis.Sarif.Location>
            {
                loc
            };
            resultItem.SetProperty("DevSkimSeverity", issue.Issue.Rule.Severity.ToString());
            resultItem.SetProperty("DevSkimConfidence", issue.Issue.Rule.Confidence.ToString());
            _results.Push(resultItem);
        }

        static FailureLevel DevSkimLevelToSarifLevel(Severity severity) => severity switch
        {
            var s when s.HasFlag(Severity.Critical) => FailureLevel.Error,
            var s when s.HasFlag(Severity.Important) => FailureLevel.Error,
            var s when s.HasFlag(Severity.Moderate) => FailureLevel.Warning,
            var s when s.HasFlag(Severity.BestPractice) => FailureLevel.Note,
            var s when s.HasFlag(Severity.ManualReview) => FailureLevel.Note,
            _ => FailureLevel.None
        };

        private ConcurrentStack<Result> _results = new ConcurrentStack<Result>();

        private ConcurrentDictionary<string, ReportingDescriptor> _rules = new ConcurrentDictionary<string, ReportingDescriptor>();
        private readonly GitInformation? _gitInformation;

        public string? OutputPath { get; }

        private void AddRuleToSarifRule(DevSkimRule devskimRule)
        {
            if (!_rules.ContainsKey(devskimRule.Id))
            {
                Uri helpUri = new Uri("https://github.com/Microsoft/DevSkim/blob/main/guidance/" + devskimRule.RuleInfo); ;
                ReportingDescriptor sarifRule = new ReportingDescriptor();
                sarifRule.Id = devskimRule.Id;
                sarifRule.Name = ToSarifFriendlyName(devskimRule.Name);
                sarifRule.ShortDescription = new MultiformatMessageString() { Text = devskimRule.Description };
                sarifRule.FullDescription = new MultiformatMessageString() { Text = $"{devskimRule.Name}: {devskimRule.Description}" };
                sarifRule.Help = new MultiformatMessageString()
                {
                    // If recommendation is present use that, otherwise use description if present, otherwise use the HelpUri
                    Text = !string.IsNullOrEmpty(devskimRule.Recommendation) ? devskimRule.Recommendation : 
                        (!string.IsNullOrEmpty(devskimRule.Description) ? devskimRule.Description : $"Visit {helpUri} for guidance on this issue."),
                    Markdown = $"Visit [{helpUri}]({helpUri}) for guidance on this issue."
                };
                sarifRule.HelpUri = helpUri;
                sarifRule.DefaultConfiguration = new ReportingConfiguration()
                {
                    Enabled = true,
                    Level = DevSkimLevelToSarifLevel(devskimRule.Severity)
                };
                // Set github code scanning properties
                sarifRule.SetProperty("precision", ConfidenceToPrecision(devskimRule.Confidence));
                sarifRule.SetProperty("problem.severity", DevSkimLevelToGitHubLevel(devskimRule.Severity));
                sarifRule.SetProperty("DevSkimSeverity", devskimRule.Severity.ToString());
                sarifRule.SetProperty("DevSkimConfidence", devskimRule.Confidence.ToString());

                _rules.TryAdd(devskimRule.Id, sarifRule);
            }
        }

        private object DevSkimLevelToGitHubLevel(Severity severity) => severity switch
        {
            Severity.Unspecified => string.Empty,
            Severity.Critical => "error",
            Severity.Important => "warning",
            Severity.Moderate => "warning",
            Severity.BestPractice => "recommendation",
            Severity.ManualReview => "recommendation",
            _ => string.Empty,
        };

        private static string ConfidenceToPrecision(Confidence confidence) => confidence switch
        {
            Confidence.High => "high",
            Confidence.Medium => "medium",
            Confidence.Low => "low",
            Confidence.Unspecified => string.Empty,
            _ => string.Empty
        };

        private string ToSarifFriendlyName(string devskimRuleName) =>
            string.Concat(devskimRuleName.Split(' ', StringSplitOptions.RemoveEmptyEntries)
                .Select(x => string.Concat(x.Where(char.IsLetterOrDigit)))
                .Select(word => string.IsNullOrEmpty(word) ? string.Empty : 
                    word.Length == 1 ? word : $"{word[..1].ToUpper()}{word[1..].ToLower()}"));

        /// <summary>
        /// Gets deduplicated set of fixes for the issue
        /// </summary>
        /// <param name="issue"></param>
        /// <returns></returns>
        private List<Fix> GetFixits(IssueRecord issue)
        {
            HashSet<Fix> fixes = new HashSet<Fix>();
            if (issue.Issue.Rule.Fixes != null)
            {
                foreach (CodeFix fix in issue.Issue.Rule.Fixes.Where(codeFix => DevSkimRuleProcessor.IsFixable(issue.TextSample, codeFix)))
                {
                    List<Replacement> replacements = new List<Replacement>();
                    var potentialReplacement = DevSkimRuleProcessor.Fix(issue.TextSample, fix);
                    if (potentialReplacement is { })
                    {
                        replacements.Add(new Replacement(new Region()
                        {
                            CharOffset = issue.Issue.Boundary.Index,
                            CharLength = issue.Issue.Boundary.Length,
                        }, new ArtifactContent() { Text =  potentialReplacement}, null));

                        ArtifactChange[] changes = new ArtifactChange[]
                        {
                            new ArtifactChange(
                                GetValueAndImplicitlyPopulateCache(issue.Filename),
                                replacements,
                                null)
                        };

                        fixes.Add(new Fix()
                        {
                            ArtifactChanges = changes,
                            Description = new Message() { Text = issue.Issue.Rule.Description }
                        });
                    }
                }
            }
            return fixes.ToList();
        }

        private void MapRuleToResult(Rule rule, ref Result resultItem)
        {
            switch (rule.Severity)
            {
                case Severity.Critical:
                case Severity.Important:
                case Severity.Moderate:
                    resultItem.Level = FailureLevel.Error;
                    break;

                case Severity.BestPractice:
                    resultItem.Level = FailureLevel.Warning;
                    break;

                default:
                    resultItem.Level = FailureLevel.Note;
                    break;
            }

            resultItem.RuleId = rule.Id;
            resultItem.Message = new Message() { Text = rule.Name };
            foreach (string tag in rule.Tags ?? Array.Empty<string>())
            {
                resultItem.Tags.Add(tag);
            }
        }
    }
}