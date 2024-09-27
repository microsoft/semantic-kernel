// Copyright (C) Microsoft. All rights reserved. Licensed under the MIT License.

using System;
using System.IO;
using System.Linq;
using System.Text;
using Microsoft.CodeAnalysis.Sarif;
using Microsoft.DevSkim.CLI.Options;
using Microsoft.Extensions.Logging;

namespace Microsoft.DevSkim.CLI.Commands
{
    public class FixCommand
    {
        private readonly FixCommandOptions _opts;
        private readonly ILoggerFactory _logFactory;
        private readonly ILogger<FixCommand> _logger;

        /// <summary>
        /// Create an instance of a command to apply fixes from detections in a DevSkim AnalyzeCommand output Sarif
        /// </summary>
        /// <param name="options"></param>
        public FixCommand(FixCommandOptions options)
        {
            _opts = options;
            _logFactory = _opts.GetLoggerFactory();
            _logger = _logFactory.CreateLogger<FixCommand>();
        }

        /// <summary>
        /// Apply fixes as specified by the FixCommandOptions
        /// </summary>
        /// <returns></returns>
        public int Run()
        {
            SarifLog sarifLog = SarifLog.Load(_opts.SarifInput);
            if (sarifLog.Runs.Count > 0)
            {
                Run run = sarifLog.Runs[0];
                System.Collections.Generic.IEnumerable<IGrouping<Uri, Result>> groupedResults = run.Results.GroupBy(x => x.Locations[0].PhysicalLocation.ArtifactLocation.Uri);
                if (!_opts.ApplyAllFixes && !_opts.FilesToApplyTo.Any() && !_opts.RulesToApplyFrom.Any())
                {
                    _logger.LogError("Must specify either apply all fixes or a combination of file and rules to apply");
                    return (int)ExitCode.CriticalError;
                }

                if (_opts.FilesToApplyTo.Any())
                {
                    groupedResults =
                        groupedResults.Where(x => _opts.FilesToApplyTo.Any(y => x.Key.AbsolutePath.Contains(y)));
                }

                if (_opts.RulesToApplyFrom.Any())
                {
                    groupedResults = groupedResults.Where(x =>
                        _opts.RulesToApplyFrom.Any(y =>
                            x.Any(z =>
                                z.RuleId == y)));
                }

                groupedResults = groupedResults.ToList();
                foreach (IGrouping<Uri, Result> resultGroup in groupedResults)
                {
                    Uri fileName = resultGroup.Key;
                    string potentialPath = Path.Combine(_opts.Path, fileName.OriginalString);
                    // Flatten all the replacements into a single list
                    System.Collections.Generic.List<Replacement> listOfReplacements = resultGroup.Where(x => x.Fixes is { }).SelectMany(x =>
                        x.Fixes.SelectMany(y => y.ArtifactChanges)
                            .SelectMany(z => z.Replacements)).ToList();
                    // Order the results by the character offset
                    listOfReplacements.Sort((a, b) => a.DeletedRegion.CharOffset - b.DeletedRegion.CharOffset);

                    if (File.Exists(potentialPath))
                    {
                        string theContent = File.ReadAllText(potentialPath);
                        // CurPos tracks the current position in the original string
                        int curPos = 0;
                        StringBuilder sb = new StringBuilder();
                        foreach (Replacement? replacement in listOfReplacements)
                        {
                            // The replacements were sorted, so this indicates a second replacement option for the same region
                            // TODO: Improve a way to not always take the first replacement, perhaps using tags for ranking
                            if (replacement.DeletedRegion.CharOffset < curPos)
                            {
                                continue;
                            }
                            sb.Append(theContent[curPos..replacement.DeletedRegion.CharOffset]);
                            sb.Append(replacement.InsertedContent.Text);
                            if (_opts.DryRun)
                            {
                                _logger.LogInformation($"{potentialPath} will be changed: {theContent[replacement.DeletedRegion.CharOffset..(replacement.DeletedRegion.CharOffset + replacement.DeletedRegion.CharLength)]}->{replacement.InsertedContent.Text} @ {replacement.DeletedRegion.CharOffset}");
                            }
                            // CurPos tracks position in the original string,
                            // so we only want to move forward the length of the original deleted content, not the new content
                            curPos = replacement.DeletedRegion.CharOffset + replacement.DeletedRegion.CharLength;
                        }

                        sb.Append(theContent[curPos..]);

                        if (!_opts.DryRun)
                        {
                            File.WriteAllText(potentialPath, sb.ToString());
                        }
                    }
                    else
                    {
                        _logger.LogError($"{potentialPath} specified in sarif does not appear to exist on disk.");
                    }
                }
            }

            return (int)ExitCode.NoIssues;
        }
    }
}