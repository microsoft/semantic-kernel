using System.Collections.Generic;

namespace Microsoft.DevSkim.LanguageProtoInterop
{
    /// <summary>
    /// When updating this Interface ensure UpdateSettingsGenerator can handle any types here
    /// </summary>
    public interface IDevSkimOptions
    {
        public bool EnableCriticalSeverityRules { get; set; }
        public bool EnableImportantSeverityRules { get; set; }
        public bool EnableModerateSeverityRules { get; set; }
        public bool EnableManualReviewSeverityRules { get; set; }
        public bool EnableBestPracticeSeverityRules { get; set; }
        public bool EnableHighConfidenceRules { get; set; }
        public bool EnableMediumConfidenceRules { get; set; }
        public bool EnableLowConfidenceRules { get; set; }
        public string CustomRulesPathsString { get; set; }
        public string CustomLanguagesPath { get; set; }
        public string CustomCommentsPath { get; set; }
        public int SuppressionDurationInDays { get; set; }
        public CommentStylesEnum SuppressionCommentStyle { get; set; }
        public string ManualReviewerName { get; set; }
        public string GuidanceBaseURL { get; set; }
        public string IgnoreFilesString { get; set; }
        public string IgnoreRulesListString { get; set; }
        public bool IgnoreDefaultRules { get; set; }
        public bool RemoveFindingsOnClose { get; set; }
        public bool ScanOnOpen { get; set; }
        public bool ScanOnSave { get; set; }
        public bool ScanOnChange { get; set; }
    }
}