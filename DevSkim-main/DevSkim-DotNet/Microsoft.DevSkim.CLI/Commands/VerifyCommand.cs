// Copyright (C) Microsoft. All rights reserved. Licensed under the MIT License.

using System;
using System.Linq;
using Microsoft.ApplicationInspector.RulesEngine;
using Microsoft.DevSkim.CLI.Options;
using Microsoft.Extensions.Logging;

namespace Microsoft.DevSkim.CLI.Commands
{
    public class VerifyCommand
    {
        private readonly VerifyCommandOptions _opts;
        private readonly ILoggerFactory _logFactory;
        private readonly ILogger<VerifyCommand> _logger;
        /// <summary>
        /// Create a Verify command Verify DevSkim rules for validity
        /// </summary>
        /// <param name="options"></param>
        public VerifyCommand(VerifyCommandOptions options)
        {
            _opts = options;
            _logFactory = _opts.GetLoggerFactory();
            _logger = _logFactory.CreateLogger<VerifyCommand>();
        }

        /// <summary>
        /// Execute the verification
        /// </summary>
        /// <returns>An int representation of a <see cref="ExitCode"/></returns>
        public int Run()
        {
            if (!string.IsNullOrEmpty(_opts.CommentsPath) ^ !string.IsNullOrEmpty(_opts.LanguagesPath))
            {
                _logger.LogError("If languages or comments are specified both must be specified.");
                return (int)ExitCode.ArgumentParsingError;
            }

            DevSkimRuleSet devSkimRuleSet = new();

            foreach (string path in _opts.Rules)
            {
                devSkimRuleSet.AddPath(path);
            }

            DevSkimRuleVerifier devSkimVerifier = new DevSkimRuleVerifier(new DevSkimRuleVerifierOptions()
            {
                LanguageSpecs = !string.IsNullOrEmpty(_opts.CommentsPath) && !string.IsNullOrEmpty(_opts.LanguagesPath) ? DevSkimLanguages.FromFiles(_opts.CommentsPath, _opts.LanguagesPath) : DevSkimLanguages.LoadEmbedded(),
                LoggerFactory = _logFactory
            });

            DevSkimRulesVerificationResult result = devSkimVerifier.Verify(devSkimRuleSet);

            if (!result.Verified)
            {
                _logger.LogError("Rules failed validation. ");
                foreach (RuleStatus status in result.DevSkimRuleStatuses)
                {
                    if (!status.Verified)
                    {
                        foreach (string error in status.Errors)
                        {
                            _logger.LogError(error);
                        }
                    }

                    return (int)ExitCode.IssuesExists;
                }
            }

            _logger.LogInformation("{0} of {1} rules have must-match self-tests.", result.DevSkimRuleStatuses.Count(x => x.HasPositiveSelfTests), result.DevSkimRuleStatuses.Count);
            _logger.LogInformation("{0} of {1} rules have must-not-match self-tests.", result.DevSkimRuleStatuses.Count(x => x.HasNegativeSelfTests), result.DevSkimRuleStatuses.Count);

            if (!devSkimRuleSet.Any())
            {
                _logger.LogError("Error: No rules were loaded. ");
                return (int)ExitCode.CriticalError;
            }

            return (int)ExitCode.NoIssues;
        }
    }
}