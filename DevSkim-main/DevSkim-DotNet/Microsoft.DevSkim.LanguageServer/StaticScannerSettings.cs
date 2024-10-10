using GlobExpressions;
using Microsoft.DevSkim.LanguageProtoInterop;

namespace DevSkim.LanguageServer
{
    using Microsoft.ApplicationInspector.RulesEngine;
    using Microsoft.DevSkim;
    using System;
    using System.Collections.Generic;
    using System.Text.RegularExpressions;

    internal static class StaticScannerSettings
    {
        internal static SuppressionStyle SuppressionStyle { get; set; } = SuppressionStyle.Line;
        internal static ICollection<string> CustomRulePaths { get; set; } = Array.Empty<string>();
        internal static ICollection<string> IgnoreRuleIds { get; set; } = Array.Empty<string>();
        internal static ICollection<Glob> IgnoreFiles { get; set; } = Array.Empty<Glob>();
        // Used to populate suppressions
        internal static string ReviewerName { get; set; } = string.Empty;
        // Suppression duration in days
        internal static int SuppressionDuration { get; set; } = 30;
        internal static bool IgnoreDefaultRuleSet { get; set; } = false;
        internal static bool ScanOnOpen { get; set; } = true;
        internal static bool ScanOnSave { get; set; } = true;
        internal static bool ScanOnChange { get; set; } = true;
        internal static bool RemoveFindingsOnClose { get; set; } = true;
        internal static DevSkimRuleSet RuleSet { get; set; } = new DevSkimRuleSet();
        internal static DevSkimRuleProcessorOptions RuleProcessorOptions { get; set; } = new DevSkimRuleProcessorOptions();
        internal static DevSkimRuleProcessor Processor { get; set; } = new DevSkimRuleProcessor(DevSkimRuleSet.GetDefaultRuleSet(), new DevSkimRuleProcessorOptions());

        public static void UpdateWith(PortableScannerSettings request)
        {
            SuppressionStyle = ToSuppressionStyle(request.SuppressionCommentStyle);
            CustomRulePaths = request.CustomRulesPathsString.Split(',');
            IgnoreRuleIds = request.IgnoreRulesListString.Split(',');
            IgnoreFiles = request.IgnoreFilesString.Split(',').Select(x => new Glob(x)).ToArray();
            ReviewerName = request.ManualReviewerName;
            SuppressionDuration = request.SuppressionDurationInDays;
            IgnoreDefaultRuleSet = request.IgnoreDefaultRules;
            ScanOnOpen = request.ScanOnOpen;
            ScanOnSave = request.ScanOnSave;
            ScanOnChange = request.ScanOnChange;
            RemoveFindingsOnClose = request.RemoveFindingsOnClose;
            RuleProcessorOptions.SeverityFilter = ParseSeverity(request);
            RuleProcessorOptions.ConfidenceFilter = ParseConfidence(request);
            try
            {
                RuleProcessorOptions.Languages = !string.IsNullOrEmpty(request.CustomCommentsPath) && !string.IsNullOrEmpty(request.CustomLanguagesPath) ? DevSkimLanguages.FromFiles(commentsPath: request.CustomCommentsPath,
                    languagesPath: request.CustomLanguagesPath) : DevSkimLanguages.LoadEmbedded();
            }
            catch
            {
                RuleProcessorOptions.Languages = DevSkimLanguages.LoadEmbedded();
                // TODO: Surface this error
            }

            DevSkimRuleSet ruleSet = IgnoreDefaultRuleSet ? new DevSkimRuleSet() : DevSkimRuleSet.GetDefaultRuleSet();
            foreach (string path in CustomRulePaths)
            {
                try
                {
                    ruleSet.AddPath(path);
                }
                catch
                {
                    // TODO: Log issue with provided path
                }
            }

            ruleSet = ruleSet.WithoutIds(IgnoreRuleIds);
            RuleSet = ruleSet;
            Processor = new DevSkimRuleProcessor(RuleSet, RuleProcessorOptions);
        }

        private static SuppressionStyle ToSuppressionStyle(CommentStylesEnum suppressionCommentStyle)
        {
            return suppressionCommentStyle switch
            {
                CommentStylesEnum.Line => SuppressionStyle.Line,
                CommentStylesEnum.Block => SuppressionStyle.Block,
                _ => throw new NotImplementedException()
            };
        }

        private static Confidence ParseConfidence(PortableScannerSettings request)
        {
            Confidence confidence = Confidence.Unspecified;
            if (request.EnableHighConfidenceRules)
            {
                confidence |= Confidence.High;
            }
            if (request.EnableMediumConfidenceRules)
            {
                confidence |= Confidence.Medium;
            }
            if (request.EnableLowConfidenceRules)
            {
                confidence |= Confidence.Low;
            }
            return confidence;
        }

        private static Severity ParseSeverity(PortableScannerSettings request)
        {
            Severity severity = Severity.Unspecified;
            if (request.EnableCriticalSeverityRules)
            {
                severity |= Severity.Critical;
            }
            if (request.EnableImportantSeverityRules)
            {
                severity |= Severity.Important;
            }
            if (request.EnableManualReviewSeverityRules)
            {
                severity |= Severity.ManualReview;
            }
            if (request.EnableModerateSeverityRules)
            {
                severity |= Severity.Moderate;
            }
            if (request.EnableBestPracticeSeverityRules)
            {
                severity |= Severity.BestPractice;
            }
            return severity;
        }
    }
}
