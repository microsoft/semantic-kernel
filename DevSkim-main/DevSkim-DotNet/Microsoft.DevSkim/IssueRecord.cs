// Copyright (C) Microsoft. All rights reserved. Licensed under the MIT License.

using System.Collections.Generic;

namespace Microsoft.DevSkim
{
    public class IssueRecord
    {
        public IssueRecord(string Filename, int Filesize, string TextSample, Issue Issue, string Language,
            List<CodeFix>? Fixes)
        {
            this.Filename = Filename;
            this.Filesize = Filesize;
            this.TextSample = TextSample;
            this.Issue = Issue;
            this.Language = Language;
        }
        public string Filename { get; }
        public int Filesize { get; }
        public Issue Issue { get; }
        public string Language { get; }
        public string TextSample { get; }
    }
}