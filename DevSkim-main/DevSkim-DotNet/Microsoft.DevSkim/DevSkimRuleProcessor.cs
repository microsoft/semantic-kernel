using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using Microsoft.ApplicationInspector.RulesEngine;
using Microsoft.CST.RecursiveExtractor;

namespace Microsoft.DevSkim
{
    public class DevSkimRuleProcessor
    {
        private readonly RuleProcessor _aiProcessor;
        private Languages _languages => _processorOptions.Languages;
        private readonly DevSkimRuleProcessorOptions _processorOptions;

        public DevSkimRuleProcessor(DevSkimRuleSet ruleSet, DevSkimRuleProcessorOptions processorOptions)
        {
            _aiProcessor = new RuleProcessor(ruleSet, processorOptions);
            _processorOptions = processorOptions;
        }

        public IEnumerable<Issue> Analyze(string text, string fileName)
        {
            List<Issue> resultsList = new List<Issue>();
            if (_languages.FromFileNameOut(fileName, out LanguageInfo info))
            {
                // Create a textcontainer
                TextContainer textContainer = new TextContainer(text, info.Name, _languages, _processorOptions.LoggerFactory);
                // Get AI Issues
                // -1 NumLinesContext disables all sample gathering
                List<MatchRecord> matchRecords = _aiProcessor.AnalyzeFile(textContainer, new FileEntry(fileName, new MemoryStream()),
                    info, null, numLinesContext: -1);
                // Apply suppressions
                foreach (MatchRecord matchRecord in matchRecords)
                {
                    if (matchRecord.Rule is DevSkimRule devSkimRule)
                    {
                        Issue issue = new Issue(Boundary: matchRecord.Boundary,
                        StartLocation: textContainer.GetLocation(matchRecord.Boundary.Index),
                        EndLocation: textContainer.GetLocation(matchRecord.Boundary.Index + matchRecord.Boundary.Length),
                        Rule: devSkimRule);
                        // Match record confidence is based on pattern confidence (from AI engine)
                        // As a backup, DevSkim Rules may also have an overall confidence specified for the rule, use that when match confidence undefined
                        issue.Confidence = matchRecord.Confidence == Confidence.Unspecified ? devSkimRule.Confidence : matchRecord.Confidence;
                        if (_processorOptions.EnableSuppressions)
                        {
                            Suppression supp = new(textContainer, issue.StartLocation.Line);
                            SuppressedIssue? supissue = supp.GetSuppressedIssue(issue.Rule.Id);
                            if (supissue is null)
                            {
                                resultsList.Add(issue);
                            }
                            //Otherwise add the suppression info instead
                            else
                            {
                                issue.IsSuppressionInfo = true;

                                if (!resultsList.Any(x =>
                                        x.Rule.Id == issue.Rule.Id && x.Boundary.Index == issue.Boundary.Index))
                                {
                                    resultsList.Add(issue);
                                }
                            }
                        }
                        else
                        {
                            resultsList.Add(issue);
                        }
                    }
                }
            }

            return resultsList;
        }

        /// <summary>
        ///     Applies given fix on the provided source code line.
        ///     Recommended to call <see cref="IsFixable"/> first to ensure the fix is intended for the target.
        /// </summary>
        /// <param name="text"> Source code line </param>
        /// <param name="fixRecord"> Fix record to be applied </param>
        /// <returns> Fixed source code line </returns>
        public static string? Fix(string text, CodeFix fixRecord)
        {
            string? result = null;

            if (fixRecord?.FixType is { } and FixType.RegexReplace)
            {
                if (fixRecord.Pattern is { } fixPattern)
                {
                    Regex? regex = SearchPatternToRegex(fixPattern);
                    if (regex is { })
                    {
                        result = regex.Replace(text, fixRecord.Replacement ?? string.Empty);
                    }
                }
            }

            return result;
        }

        private static Regex? SearchPatternToRegex(SearchPattern pattern)
        {
            RegexOptions options = RegexOptions.None;
            if (pattern.Modifiers.Contains("i"))
            {
                options |= RegexOptions.IgnoreCase;
            }
            if (pattern.Modifiers.Contains("m"))
            {
                options |= RegexOptions.Multiline;
            }

            if (pattern.Pattern is { })
            {
                try
                {
                    Regex regex = new Regex(pattern.Pattern, options);
                    return regex;
                }
                catch (Exception e)
                {
                    // failed to construct regex for fix
                }    
            }

            return null;
        }

        /// <summary>
        ///     Checks if the target source can be fixed with the provided fix
        /// </summary>
        /// <param name="text"> Source code line </param>
        /// <param name="fixRecord"> Fix record to be applied </param>
        /// <returns> Fixed source code line </returns>
        public static bool IsFixable(string text, CodeFix fixRecord)
        {
            if (fixRecord?.FixType is { } fr && fr == FixType.RegexReplace)
            {
                if (fixRecord.Pattern is { } fixPattern)
                {
                    Regex? regex = SearchPatternToRegex(fixPattern);
                    if (regex is { })
                    {
                        return regex.IsMatch(text);
                    }
                }
            }

            return false;
        }



        /// <summary>
        ///     Generate appropriate suppression with comment style based on the filename
        /// </summary>
        /// <param name="fileName"></param>
        /// <param name="rulesId"></param>
        /// <param name="preferMultiLine"></param>
        /// <param name="duration"></param>
        /// <param name="reviewerName"></param>
        /// <param name="languages"></param>
        /// <returns></returns>
        public static string GenerateSuppressionByFileName(string fileName, string rulesId, bool preferMultiLine = false, int duration = 0, string? reviewerName = null, Languages? languages = null)
        {
            languages ??= DevSkimLanguages.LoadEmbedded();
            if (languages.FromFileNameOut(fileName, out LanguageInfo info))
            {
                return GenerateSuppressionByLanguage(info.Name, rulesId, preferMultiLine, duration, reviewerName, languages);
            }

            return string.Empty;
        }

        /// <summary>
        ///     Generate suppression text for a given rule ID and language. 
        ///     If the comment style for the language is not specified, returns null.
        /// </summary>
        /// <param name="sourceLanguage">The target language (to choose the right comment style)</param>
        /// <param name="rulesId">The ID for the rule to suppress</param>
        /// <param name="preferMultiLine">If multiline comment style should be preferred</param>
        /// <param name="duration">Duration in days for suppression. Default 0 (unlimited)</param>
        /// <param name="reviewerName">Optional name for the manual reviewer applying suppressions</param>
        /// <param name="languages">Optional language specifications to use</param>
        /// <returns>A comment suppression or null if one could not be generated</returns>
        public static string GenerateSuppressionByLanguage(string sourceLanguage, string rulesId, bool preferMultiLine = false, int duration = 0, string? reviewerName = null, Languages? languages = null)
        {
            languages ??= DevSkimLanguages.LoadEmbedded();
            string inline = languages.GetCommentInline(sourceLanguage);
            string expiration = duration > 0 ? DateTime.Now.AddDays(duration).ToString("yyyy-MM-dd") : string.Empty;
            StringBuilder sb = new StringBuilder();
            (string prefix, string suffix) = (preferMultiLine || string.IsNullOrEmpty(inline)) ?
                (languages.GetCommentPrefix(sourceLanguage), languages.GetCommentSuffix(sourceLanguage)) :
                (languages.GetCommentInline(sourceLanguage), string.Empty);

            sb.Append($"{prefix} DevSkim: ignore {rulesId}");

            if (!string.IsNullOrEmpty(expiration))
            {
                sb.Append($" until {expiration}");
            }
            if (!string.IsNullOrEmpty(reviewerName))
            {
                sb.Append($" by {reviewerName}");
            }
            if (!string.IsNullOrEmpty(suffix))
            {
                sb.Append($" {suffix}");
            }
            return sb.ToString();
        }
    }
}