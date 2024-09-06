// Copyright (C) Microsoft. All rights reserved. Licensed under the MIT License.

using Microsoft.CodeAnalysis.Sarif;
using Microsoft.DevSkim.CLI.Commands;
using System.Text;
using Microsoft.DevSkim.CLI;
using Microsoft.DevSkim.CLI.Options;

namespace Microsoft.DevSkim.Tests
{
    [TestClass]
    public class AnalyzeTest
    {
        [TestMethod]
        public void RelativePathTest()
        {
            string tempFileName = $"{Path.GetTempFileName()}.cs";
            string outFileName = Path.GetTempFileName();
            // GetTempFileName actually makes the file
            File.Delete(outFileName);

            string basePath = Path.GetTempPath();
            string oneUpPath = Directory.GetParent(basePath).FullName;
            using FileStream file = File.Open(tempFileName, FileMode.Create);
            file.Write(Encoding.UTF8.GetBytes("MD5;\nhttp://contoso.com\n"));
            file.Close();

            AnalyzeCommandOptions opts = new AnalyzeCommandOptions()
            {
                Path = tempFileName,
                OutputFile = outFileName,
                OutputFileFormat = "sarif",
                BasePath = basePath
            };
            new AnalyzeCommand(opts).Run();

            SarifLog resultsFile = SarifLog.Load(outFileName);
            Assert.AreEqual(1, resultsFile.Runs.Count);
            Assert.AreEqual(2, resultsFile.Runs[0].Results.Count);
            Assert.AreEqual(Path.GetFileName(tempFileName), resultsFile.Runs[0].Results[0].Locations[0].PhysicalLocation.ArtifactLocation.Uri.ToString());

            string outFileName2 = Path.GetTempFileName();

            opts = new AnalyzeCommandOptions()
            {
                Path = tempFileName,
                OutputFile = outFileName2,
                OutputFileFormat = "sarif",
                AbsolutePaths = true
            };
            new AnalyzeCommand(opts).Run();

            resultsFile = SarifLog.Load(outFileName2);
            Assert.AreEqual(1, resultsFile.Runs.Count);
            Assert.AreEqual(2, resultsFile.Runs[0].Results.Count);
            Assert.AreEqual(new Uri(tempFileName).GetFilePath(), resultsFile.Runs[0].Results[0].Locations[0].PhysicalLocation.ArtifactLocation.Uri.GetFilePath());

            string outFileName3 = Path.GetTempFileName();

            opts = new AnalyzeCommandOptions()
            {
                Path = tempFileName,
                OutputFile = outFileName3,
                OutputFileFormat = "sarif"
            };
            new AnalyzeCommand(opts).Run();

            resultsFile = SarifLog.Load(outFileName3);
            Assert.AreEqual(1, resultsFile.Runs.Count);
            Assert.AreEqual(2, resultsFile.Runs[0].Results.Count);
            // If no base path is specified, the base path is rooted in by the Path argument
            Assert.AreEqual(Path.GetFileName(tempFileName), resultsFile.Runs[0].Results[0].Locations[0].PhysicalLocation.ArtifactLocation.Uri.GetFilePath());

            string outFileName4 = Path.GetTempFileName();

            opts = new AnalyzeCommandOptions()
            {
                Path = tempFileName,
                OutputFile = outFileName4,
                OutputFileFormat = "sarif",
                BasePath = Directory.GetCurrentDirectory()
            };
            new AnalyzeCommand(opts).Run();

            resultsFile = SarifLog.Load(outFileName4);
            Assert.AreEqual(1, resultsFile.Runs.Count);
            Assert.AreEqual(2, resultsFile.Runs[0].Results.Count);

            // The path to CWD isnt relative 
            Assert.AreEqual(resultsFile.Runs[0].Results[0].Locations[0].PhysicalLocation.ArtifactLocation.Uri.GetFilePath(), Path.GetRelativePath(Directory.GetCurrentDirectory(), tempFileName));
        }

        public const string contentToTest = @"MD5;
// MD5
/* MD5
*/";

        public const string languageFileContent = @"[
    {
        ""name"": ""lorem"",
        ""extensions"": [ "".xx"" ]
    }
]";

        public const string commentFileContent = @"[
    {
        ""language"": 
        [
            ""lorem""
        ],
        ""inline"": ""//"",
        ""prefix"": ""/*"",
        ""suffix"": ""*/""
    }
  ]";

        public const string ruleFileContent = @"[
    {
        ""name"": ""Win32 - Hard-coded SSL/TLS Protocol"",
        ""id"": ""DSTEST"",
        ""description"": ""Test rule that should match cs but not other languages"",
        ""applies_to"": [
            ""lorem""
        ],
        ""tags"": [
            ""Tests.LanguagesAndComments""
        ],
        ""severity"": ""ManualReview"",
        ""confidence"" : ""High"",
        ""rule_info"": ""DSTEST.md"",
        ""patterns"": [
            {
                ""pattern"": ""MD5"",
                ""type"": ""regex"",
                ""scopes"": [
                    ""code""
                ]
            }
        ]
    }
]";

        [DataRow(commentFileContent, languageFileContent, ruleFileContent, (int)ExitCode.Okay, 1)]
        [DataRow(languageFileContent, commentFileContent, ruleFileContent, (int)ExitCode.CriticalError, 1)]
        [DataRow(commentFileContent, commentFileContent, ruleFileContent, (int)ExitCode.CriticalError, 1)]
        [DataRow(languageFileContent, languageFileContent, ruleFileContent, (int)ExitCode.Okay, 3)] // We would expect this to fail, but failing to deserialize comments fails open currently in AI, thus comments are ignored, thus 3 results

        [DataTestMethod]
        public void TestCustomLanguageAndComments(string commentFileContentIn, string languageFileContentIn, string ruleFileContentIn, int expectedExitCode, int expectedNumResults)
        {
            string tempFileName = PathHelper.GetRandomTempFile("xx");
            string languagesFileName = PathHelper.GetRandomTempFile("json");
            string commentsFileName = PathHelper.GetRandomTempFile("json");
            string ruleFileName = PathHelper.GetRandomTempFile("json");
            string outFileName = PathHelper.GetRandomTempFile("sarif");
            using FileStream file = File.Open(tempFileName, FileMode.Create);
            file.Write(Encoding.UTF8.GetBytes(contentToTest));
            file.Close();
            using FileStream languageFile = File.Open(languagesFileName, FileMode.Create);
            languageFile.Write(Encoding.UTF8.GetBytes(languageFileContentIn));
            languageFile.Close();
            using FileStream commentsFile = File.Open(commentsFileName, FileMode.Create);
            commentsFile.Write(Encoding.UTF8.GetBytes(commentFileContentIn));
            commentsFile.Close();
            using FileStream ruleFile = File.Open(ruleFileName, FileMode.Create);
            ruleFile.Write(Encoding.UTF8.GetBytes(ruleFileContentIn));
            ruleFile.Close();
            AnalyzeCommandOptions opts = new AnalyzeCommandOptions()
            {
                Path = tempFileName,
                OutputFile = outFileName,
                OutputFileFormat = "sarif",
                CommentsPath = commentsFileName,
                LanguagesPath = languagesFileName,
                Rules = new[] { ruleFileName },
                IgnoreDefaultRules = true
            };
            new AnalyzeCommand(opts).Run();

            int resultCode = new AnalyzeCommand(opts).Run();
            Assert.AreEqual(expectedExitCode, resultCode);
            if (expectedExitCode == 0)
            {
                SarifLog resultsFile = SarifLog.Load(outFileName);
                Assert.AreEqual(1, resultsFile.Runs.Count);
                Assert.AreEqual(expectedNumResults, resultsFile.Runs[0].Results.Count);
                if (expectedNumResults > 0)
                {
                    Assert.AreEqual("DSTEST", resultsFile.Runs[0].Results[0].RuleId);
                }
            }
        }

        [DataTestMethod]
        [DataRow("DS126858", "DS126858")]
        [DataRow("DS137138", "DS137138")]
        public void TestFilterByIds(string idToLimitTo, string idToExpect)
        {
            string tempFileName = $"{Path.GetTempFileName()}.cs";
            string outFileName = Path.GetTempFileName();
            // GetTempFileName actually makes the file
            File.Delete(outFileName);
            using FileStream file = File.Open(tempFileName, FileMode.Create);
            file.Write(Encoding.UTF8.GetBytes("MD5;\nhttp://contoso.com\n"));
            file.Close();

            AnalyzeCommandOptions opts = new AnalyzeCommandOptions()
            {
                Path = tempFileName,
                OutputFile = outFileName,
                OutputFileFormat = "sarif",
                RuleIds = new[] { idToLimitTo }
            };
            new AnalyzeCommand(opts).Run();

            int resultCode = new AnalyzeCommand(opts).Run();
            Assert.AreEqual(0, resultCode);
            SarifLog resultsFile = SarifLog.Load(outFileName);
            Assert.AreEqual(1, resultsFile.Runs.Count);
            Assert.AreEqual(1, resultsFile.Runs[0].Results.Count);
            Assert.AreEqual(idToExpect, resultsFile.Runs[0].Results[0].RuleId);
        }

        [DataTestMethod]
        [DataRow("DS126858", "DS137138")]
        [DataRow("DS137138", "DS126858")]
        public void TestIgnoreIds(string idToIgnore, string idToExpect)
        {
            string tempFileName = $"{Path.GetTempFileName()}.cs";
            string outFileName = Path.GetTempFileName();
            // GetTempFileName actually makes the file
            File.Delete(outFileName);
            using FileStream file = File.Open(tempFileName, FileMode.Create);
            file.Write(Encoding.UTF8.GetBytes("MD5;\nhttp://contoso.com\n"));
            file.Close();

            AnalyzeCommandOptions opts = new AnalyzeCommandOptions()
            {
                Path = tempFileName,
                OutputFile = outFileName,
                OutputFileFormat = "sarif",
                IgnoreRuleIds = new[] { idToIgnore }
            };
            new AnalyzeCommand(opts).Run();

            int resultCode = new AnalyzeCommand(opts).Run();
            Assert.AreEqual(0, resultCode);
            SarifLog resultsFile = SarifLog.Load(outFileName);
            Assert.AreEqual(1, resultsFile.Runs.Count);
            Assert.AreEqual(1, resultsFile.Runs[0].Results.Count);
            Assert.AreEqual(idToExpect, resultsFile.Runs[0].Results[0].RuleId);
        }
    }
}