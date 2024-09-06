using Microsoft.ApplicationInspector.RulesEngine;
using Microsoft.DevSkim;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging.Abstractions;
using System.Text.RegularExpressions;
using GlobExpressions;

namespace DevSkim.LanguageServer;

internal class ConfigHelpers
{
    /// <summary>
    /// Lists are presented in the configuration as a number of items with the name of the list appended with ':i' where i is the index of the item from the list.
    /// This method compacts those back to a Collection for convenience.
    /// </summary>
    /// <param name="configuration"></param>
    /// <param name="valueName"></param>
    /// <returns></returns>
    internal static ICollection<T> CompileList<T>(IConfiguration configuration, string valueName)
    {
        List<T> toReturn = new List<T>();
        int i = 0;
        while (true)
        {
            T nextItem = configuration.GetValue<T>($"{Section}:{valueName}:{i}");
            if (nextItem == null)
            {
                break;
            }
            else
            {
                toReturn.Add(nextItem);
                i++;
            }
        }
        return toReturn;
    }

    internal static readonly string Section = "MS-CST-E.vscode-devskim";
    internal static void SetScannerSettings(IConfiguration configuration)
    {
        StaticScannerSettings.RuleProcessorOptions = OptionsFromConfiguration(configuration);
        StaticScannerSettings.IgnoreDefaultRuleSet = configuration.GetValue<bool>($"{Section}:ignores:ignoreDefaultRules");
        StaticScannerSettings.CustomRulePaths = CompileList<string>(configuration, "rules:customRulesPaths");
        StaticScannerSettings.IgnoreRuleIds = CompileList<string>(configuration, "ignores:ignoreRulesList");
        List<Glob> fileIgnoreRegexes = new();
        foreach (string potentialRegex in CompileList<string>(configuration, "ignores:ignoreFiles"))
        {
            try
            {
                fileIgnoreRegexes.Add(new Glob(potentialRegex));
            }
            catch (Exception e)
            {
                // TODO: Log issue with provided regex
            }
        }
        StaticScannerSettings.IgnoreFiles = fileIgnoreRegexes;

        StaticScannerSettings.RemoveFindingsOnClose = configuration.GetValue<bool>($"{Section}:findings:removeFindingsOnClose");
        StaticScannerSettings.ScanOnOpen = configuration.GetValue<bool>($"{Section}:triggers:scanOnOpen");
        StaticScannerSettings.ScanOnSave = configuration.GetValue<bool>($"{Section}:triggers:scanOnSave");
        StaticScannerSettings.ScanOnChange = configuration.GetValue<bool>($"{Section}:triggers:scanOnChange");
        StaticScannerSettings.SuppressionDuration = configuration.GetValue<int>($"{Section}:suppressions:suppressionDurationInDays");
        StaticScannerSettings.SuppressionStyle = configuration.GetValue<SuppressionStyle>($"{Section}:suppressions:suppressionCommentStyle");
        StaticScannerSettings.ReviewerName = configuration.GetValue<string>($"{Section}:suppressions:manualReviewerName");

        DevSkimRuleSet ruleSet = StaticScannerSettings.IgnoreDefaultRuleSet ? new DevSkimRuleSet() : DevSkimRuleSet.GetDefaultRuleSet();
        foreach (string path in StaticScannerSettings.CustomRulePaths)
        {
            try
            {
                ruleSet.AddPath(path);
            }
            catch (Exception e)
            {
                // TODO: Log issue with provided path
            }
        }
        ruleSet = ruleSet.WithoutIds(StaticScannerSettings.IgnoreRuleIds);
        StaticScannerSettings.RuleSet = ruleSet;
        StaticScannerSettings.Processor = new DevSkimRuleProcessor(StaticScannerSettings.RuleSet, StaticScannerSettings.RuleProcessorOptions);
    }

    private static DevSkimRuleProcessorOptions OptionsFromConfiguration(IConfiguration configuration)
    {
        string languagesPath = configuration.GetValue<string>($"{Section}:rules:customLanguagesPath");
        string commentsPath = configuration.GetValue<string>($"{Section}:rules:customCommentsPath");
        Severity severityFilter = Severity.Unspecified;
        if (configuration.GetValue<bool>($"{Section}:rules:enableCriticalSeverityRules"))
        {
            severityFilter |= Severity.Critical;
        }
        if (configuration.GetValue<bool>($"{Section}:rules:enableImportantSeverityRules"))
        {
            severityFilter |= Severity.Important;
        }
        if (configuration.GetValue<bool>($"{Section}:rules:enableModerateSeverityRules"))
        {
            severityFilter |= Severity.Moderate;
        }
        if (configuration.GetValue<bool>($"{Section}:rules:enableManualReviewSeverityRules"))
        {
            severityFilter |= Severity.ManualReview;
        }
        if (configuration.GetValue<bool>($"{Section}:rules:enableBestPracticeSeverityRules"))
        {
            severityFilter |= Severity.BestPractice;
        }
        Confidence confidenceFilter = Confidence.Unspecified;
        if (configuration.GetValue<bool>($"{Section}:rules:enableHighConfidenceRules"))
        {
            confidenceFilter |= Confidence.High;
        }
        if (configuration.GetValue<bool>($"{Section}:rules:enableMediumConfidenceRules"))
        {
            confidenceFilter |= Confidence.Medium;
        }
        if (configuration.GetValue<bool>($"{Section}:rules:enableLowConfidenceRules"))
        {
            confidenceFilter |= Confidence.Low;
        }
        return new DevSkimRuleProcessorOptions()
        {
            Languages = (string.IsNullOrEmpty(languagesPath) || string.IsNullOrEmpty(commentsPath)) ? DevSkimLanguages.LoadEmbedded() : DevSkimLanguages.FromFiles(commentsPath, languagesPath),
            SeverityFilter = severityFilter,
            ConfidenceFilter = confidenceFilter,
            LoggerFactory = NullLoggerFactory.Instance,
        };
    }
}