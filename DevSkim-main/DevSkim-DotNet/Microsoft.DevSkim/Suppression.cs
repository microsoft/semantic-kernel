// Copyright (C) Microsoft. All rights reserved. Licensed under the MIT License.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;
using Microsoft.ApplicationInspector.RulesEngine;

namespace Microsoft.DevSkim
{
    /// <summary>
    ///     Processor for rule suppressions
    /// </summary>
    public class Suppression
    {
        private string _reviewer = string.Empty;
        public const string pattern = KeywordPrefix + @"\s+" + KeywordIgnore + @"\s([a-zA-Z\d,:]+)(\s+" + KeywordUntil + @"\s\d{4}-\d{2}-\d{2}|)(\s+" + KeywordBy + @"\s([A-Za-z0-9_]+)|)";

        /// <summary>
        ///     Creates new instance of Supressor
        /// </summary>
        /// <param name="text"> Text to work with </param>
        public Suppression(string text)
        {
            if (text is null)
            {
                throw new ArgumentNullException(nameof(text));
            }
            _lineText = text;
            ParseLine();
        }

        public Suppression(TextContainer text, int lineNumber)
        {
            if (text is null)
            {
                throw new ArgumentNullException(nameof(text));
            }
            _text = text;
            _lineNumber = lineNumber;
            _lineText = _text.GetLineContent(_lineNumber);

            ParseLine();
        }

        /// <summary>
        ///     Get the optional manual reviewer
        /// </summary>
        public string Reviewer
        {
            get { return _reviewer; }
        }

        /// <summary>
        ///     Suppression expiration date
        /// </summary>
        public DateTime ExpirationDate { get { return _expirationDate; } }

        /// <summary>
        ///     Suppression expresion start index on the given line
        /// </summary>
        public int Index { get { return _suppressStart; } }

        /// <summary>
        ///     Validity of suppression expresion
        /// </summary>
        /// <returns> True if suppression is in effect </returns>
        public bool IsInEffect
        {
            get
            {
                bool doesItExists = (Index >= 0 && _issues.Count > 0);
                return (doesItExists && DateTime.Now < _expirationDate);
            }
        }

        /// <summary>
        ///     Position of issues list
        /// </summary>
        public int IssuesListIndex { get; set; } = -1;

        /// <summary>
        ///     Suppression expression length
        /// </summary>
        public int Length { get { return _suppressLength; } }

        /// <summary>
        ///     Get issue IDs for the suppression
        /// </summary>
        /// <returns> List of issue IDs </returns>
        public virtual SuppressedIssue[] GetIssues()
        {
            return _issues.ToArray();
        }

        /// <summary>
        /// Check if the suppression has expired
        /// </summary>
        /// <param name="issueId"></param>
        /// <returns></returns>
        public bool IsExpired
        {
            get
            {
                bool doesItExists = (Index >= 0 && _issues.Count > 0);
                return (doesItExists && DateTime.Now > _expirationDate);
            }
        }

        /// <summary>
        ///     Test if given rule Id is being suppressed
        /// </summary>
        /// <param name="issueId"> Rule ID </param>
        /// <returns> True if rule is suppressed </returns>
        public SuppressedIssue? GetSuppressedIssue(string issueId)
        {
            SuppressedIssue? issue = _issues.FirstOrDefault(x => x.ID == issueId || x.ID == KeywordAll);
            if (DateTime.Now < _expirationDate && issue != null)
                return issue;
            else
                return null;
        }

        public string[] GetSuppressedIds => _issues.Select(x => x.ID ?? string.Empty).Where(x => !string.IsNullOrEmpty(x)).ToArray();

        protected const string KeywordAll = "all";
        protected const string KeywordIgnore = "ignore";
        protected const string KeywordPrefix = "DevSkim:";
        protected const string KeywordUntil = "until";
        protected const string KeywordBy = "by";
        protected DateTime _expirationDate { get; set; } = DateTime.MaxValue;
        protected List<SuppressedIssue> _issues { get; set; } = new List<SuppressedIssue>();
        protected int _lineNumber { get; set; }
        protected string _lineText { get; set; }
        protected int _suppressLength { get; set; } = -1;
        protected int _suppressStart { get; set; } = -1;
        protected TextContainer? _text { get; set; }
        protected Regex reg { get; set; } = new Regex(pattern, RegexOptions.IgnoreCase);

        protected void ParseLine()
        {
            Match match = reg.Match(_lineText);

            if (match.Success)
            {
                _suppressStart = match.Index;
                _suppressLength = match.Length;

                string idString = match.Groups[1].Value.Trim();
                IssuesListIndex = match.Groups[1].Index;

                // Parse Reviewer
                if (match.Groups.Count > 4 && !string.IsNullOrEmpty(match.Groups[4].Value))
                {
                    _reviewer = match.Groups[4].Value;
                }

                // Parse date
                if (match.Groups.Count > 2 && !string.IsNullOrEmpty(match.Groups[2].Value))
                {
                    string date = match.Groups[2].Value;
                    reg = new Regex(@"(\d{4}-\d{2}-\d{2})");
                    Match m = reg.Match(date);
                    if (m.Success)
                    {
                        try
                        {
                            _expirationDate = DateTime.ParseExact(m.Value, "yyyy-MM-dd", System.Globalization.CultureInfo.InvariantCulture);
                        }
                        catch (FormatException)
                        {
                            _expirationDate = DateTime.MinValue;
                        }
                    }
                }

                // parse Ids.
                if (idString == KeywordAll)
                {
                    _issues.Add(new SuppressedIssue()
                    {
                        ID = KeywordAll,
                        Boundary = new Boundary()
                        {
                            Index = IssuesListIndex,
                            Length = KeywordAll.Length
                        }
                    });
                }
                else
                {
                    string[] ids = idString.Split(',');
                    int index = IssuesListIndex;
                    foreach (string id in ids)
                    {
                        _issues.Add(new SuppressedIssue()
                        {
                            ID = id,
                            Boundary = new Boundary()
                            {
                                Index = index,
                                Length = id.Length
                            }
                        });
                        index += id.Length + 1;
                    }
                }
            }
        }
    }
}