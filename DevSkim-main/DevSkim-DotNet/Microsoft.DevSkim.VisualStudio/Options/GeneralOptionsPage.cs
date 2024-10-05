using Microsoft.DevSkim.LanguageProtoInterop;

namespace Microsoft.DevSkim.VisualStudio.Options
{
    using Microsoft.Build.Framework.XamlTypes;
    using Microsoft.VisualStudio.Shell;
    using System;
    using System.ComponentModel;
    using System.Drawing;
    using System.Runtime.InteropServices;
    using System.Windows.Forms;
    // When adding any property here, be sure to add it to IDevSkimOptions as well
    [Guid(PageGuidString)]
    public class GeneralOptionsPage : DialogPage, IDevSkimOptions
    {
        const string StringCollectionEditor = "System.Windows.Forms.Design.StringCollectionEditor, System.Design, Version=4.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a";

        [Browsable(false)]
        [DesignerSerializationVisibility(DesignerSerializationVisibility.Hidden)]
        protected override IWin32Window Window
        {
            get
            {
                PropertyGrid propertyGrid = new PropertyGrid();
                propertyGrid.Location = new Point(0, 0);
                propertyGrid.ToolbarVisible = false;
                propertyGrid.CommandsVisibleIfAvailable = false;
                propertyGrid.PropertySort = PropertySort.Categorized;
                propertyGrid.SelectedObject = AutomationObject;
                return propertyGrid;
            }
        }

        public const string PageGuidString = "c88696f6-dd46-380e-a706-14e73fd51564";
        private const string RulesCategory = "Rules";
        private const string SuppressionsCategory = "Suppressions";
        private const string GuidanceCategory = "Guidance";
        private const string IgnoresCategory = "Ignores";
        private const string FindingsCategory = "Findings";
        private const string TriggersCategory = "Triggers";

        /// <summary>
        /// Rule Options
        /// </summary>
        [Category(RulesCategory)]
        [DisplayName("Enable Critical Severity Rules")]
        [Description("Turn on the rules with severity \"Critical\".")]
        public bool EnableCriticalSeverityRules { get; set; } = true;

        [Category(RulesCategory)]
        [DisplayName("Enable Important Severity Rules")]
        [Description("Turn on the rules with severity \"Important\".")]
        public bool EnableImportantSeverityRules { get; set; } = true;

        [Category(RulesCategory)]
        [DisplayName("Enable Moderate Severity Rules")]
        [Description("Turn on the rules with severity \"Moderate\".")]
        public bool EnableModerateSeverityRules { get; set; } = true;

        [Category(RulesCategory)]
        [DisplayName("Enable Best Practice Severity Rules")]
        [Description("Turn on the rules with severity \"Best-Practice\". " +
             "These rules either flag issues that are typically of a lower severity, " +
             "or recommended practices that lead to more secure code, but aren't typically outright vulnerabilities.")]
        public bool EnableBestPracticeSeverityRules { get; set; } = true;

        [Category(RulesCategory)]
        [DisplayName("Enable Manual Review Severity Rules")]
        [Description("Turn on the rules that flag things for manual review. " +
                     "These are typically scenarios that *could* be incredibly severe if tainted data can be inserted, " +
                     "but are often programmatically necessary (for example, dynamic code generation with \"eval\").  " +
                     "Since these rules tend to require further analysis upon flagging an issue, they are disabled by default.")]
        public bool EnableManualReviewSeverityRules { get; set; } = true;

        [Category(RulesCategory)]
        [DisplayName("Enable High Confidence Rules")]
        [Description("Turn on the rules of confidence \"High\".")]
        public bool EnableHighConfidenceRules { get; set; } = true;

        [Category(RulesCategory)]
        [DisplayName("Enable Medium Confidence Rules")]
        [Description("Turn on the rules of confidence \"Medium\".")]
        public bool EnableMediumConfidenceRules { get; set; } = true;

        [Category(RulesCategory)]
        [DisplayName("Enable Low Confidence Rules")]
        [Description("Turn on the rules of confidence \"Low\".")]
        public bool EnableLowConfidenceRules { get; set; } = false;

        [Category(RulesCategory)]
        [DisplayName("Custom Rules Paths")]
        [Description("A comma separated list of local paths on disk to rules files or folders containing rule files, " +
                     "for DevSkim to use in analysis.")]
        public string CustomRulesPathsString { get; set; } = string.Empty;

        [Category(RulesCategory)]
        [DisplayName("Custom Languages Path")]
        [Description(
            "A local path to a custom language file for analysis. Also requires customCommentsPath to be set.")]
        public string CustomLanguagesPath { get; set; } = string.Empty;

        [Category(RulesCategory)]
        [DisplayName("Custom Comments Path")]
        [Description(
            "A local path to a custom comments file for analysis. Also requires customLanguagesPath to be set.")]
        public string CustomCommentsPath { get; set; } = string.Empty;


        /// <summary>
        /// Suppression Options
        /// </summary>
        [Category(SuppressionsCategory)]
        [DisplayName("Suppression Duration In Days")]
        [Description("DevSkim allows for findings to be suppressed for a temporary period of time. " +
                     "The default is 30 days. Set to 0 to disable temporary suppressions.")]
        public int SuppressionDurationInDays { get; set; } = 30;

        [Category(SuppressionsCategory)]
        [DisplayName("Suppression Comment Style")]
        [Description("When DevSkim inserts a suppression comment it defaults to using single line comments for " +
                     "every language that has them.  Setting this to 'block' will instead use block comments for the languages " +
                     "that support them.  Block comments are suggested if regularly adding explanations for why a finding " +
                     "was suppressed")]
        public CommentStylesEnum SuppressionCommentStyle { get; set; } = CommentStylesEnum.Line;

        [Category(SuppressionsCategory)]
        [DisplayName("Manual Reviewer Name")]
        [Description("If set, insert this name in inserted suppression comments.")]
        public string ManualReviewerName { get; set; } = string.Empty;


        /// <summary>
        /// Guidance Options
        /// </summary>
        [Category(GuidanceCategory)]
        [DisplayName("Guidance Base URL")]
        [Description("Each finding has a guidance file that describes the issue and solutions in more detail.  " +
                     "By default, those files live on the DevSkim github repo however, with this setting, " +
                     "organizations can clone and customize that repo, and specify their own base URL for the guidance.")]
        public string GuidanceBaseURL { get; set; } = "https://github.com/microsoft/devskim/tree/main/guidance";


        /// <summary>
        /// Ignore Options
        /// </summary>
        [Category(IgnoresCategory)]
        [DisplayName("Ignore Files by Globs")]
        [Description("Comma separated glob expression patterns to exclude files and folders which match from analysis.")]
        public string IgnoreFilesString { get; set; } = string.Empty;

        [Category(IgnoresCategory)]
        [DisplayName("Ignore Rules by Id")]
        [Description("Comma separated list of exact string identity of DevSkim Rule IDs to ignore.")]
        public string IgnoreRulesListString { get; set; } = string.Empty;

        [Category(IgnoresCategory)]
        [DisplayName("Ignore Default Rules")]
        [Description("Disable all default DevSkim rules.")]
        public bool IgnoreDefaultRules { get; set; } = false;


        /// <summary>
        /// Finding Options
        /// </summary>
        // TODO: Do we even have a scan all files in workspace type of commmand here?
        [Category(FindingsCategory)]
        [DisplayName("Remove Findings On Close")]
        [Description("By default, when a source file is closed the findings remain in the 'Error List' window.  " +
                     "Setting this value to true will cause findings to be removed from 'Error List' when the document is closed.  " +
                     "Note, setting this to true will cause findings that are listed when invoking the 'Scan all files in workspace' " +
                     "command to automatically clear away after a couple of minutes.")]
        public bool RemoveFindingsOnClose { get; set; } = true;


        /// <summary>
        /// Trigger Options
        /// </summary>
        [Category(TriggersCategory)]
        [DisplayName("Scan On Open")]
        [Description("Scan files on open.")]
        public bool ScanOnOpen { get; set; } = true;

        [Category(TriggersCategory)]
        [DisplayName("Scan On Save")]
        [Description("Scan files on save.")]
        public bool ScanOnSave { get; set; } = true;

        [Category(TriggersCategory)]
        [DisplayName("Scan On Change")]
        [Description("Scan files on change.")]
        public bool ScanOnChange { get; set; } = true;
    }
}
