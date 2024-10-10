using System;
using System.Collections.Generic;
using System.Text.RegularExpressions;

namespace Microsoft.DevSkim.LanguageProtoInterop
{
    public class PortableScannerSettings : IDevSkimOptions
    {
        public CommentStylesEnum SuppressionCommentStyle { get; set; } = CommentStylesEnum.Line;
        public string CustomRulesPathsString { get; set; } = string.Empty;
        public string IgnoreRulesListString { get; set; } = string.Empty;
        public string IgnoreFilesString { get; set; } = string.Empty;
        // Used to populate suppressions
        public string ManualReviewerName { get; set; } = string.Empty;
        // Suppression duration in days
        public int SuppressionDurationInDays { get; set; } = 30;
        public bool IgnoreDefaultRules { get; set; } = false;
        public bool ScanOnOpen { get; set; } = true;
        public bool ScanOnSave { get; set; } = true;
        public bool ScanOnChange { get; set; } = true;
        public bool RemoveFindingsOnClose { get; set; } = true;
        public string CustomLanguagesPath { get; set; } = string.Empty;
        public string CustomCommentsPath { get; set; } = string.Empty;
        public string GuidanceBaseURL { get; set; }
        public bool EnableCriticalSeverityRules { get; set; }
        public bool EnableImportantSeverityRules { get; set; }
        public bool EnableModerateSeverityRules { get; set; }
        public bool EnableManualReviewSeverityRules { get; set; }
        public bool EnableBestPracticeSeverityRules { get; set; }
        public bool EnableHighConfidenceRules { get; set; }
        public bool EnableLowConfidenceRules { get; set; }
        public bool EnableMediumConfidenceRules { get; set; }
    }
}