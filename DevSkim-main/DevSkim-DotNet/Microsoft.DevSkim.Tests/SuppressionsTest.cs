// Copyright (C) Microsoft. All rights reserved. Licensed under the MIT License.

using Microsoft.CodeAnalysis.Sarif;
using Microsoft.DevSkim.CLI.Commands;
using System.Text;
using Microsoft.DevSkim.CLI;
using Microsoft.DevSkim.CLI.Options;

namespace Microsoft.DevSkim.Tests
{
    [TestClass]
    public class SuppressionTest
    {
        [DataTestMethod]
        [DataRow("", 30)]
        [DataRow("Contoso", 30)]
        public void ExecuteSuppressionsWithReviewerNameAndDate(string reviewerName, int duration)
        {
            (string basePath, string sourceFile, string sarifPath) = runAnalysis(@"MD5;
            http://contoso.com", "c");

            SuppressionCommandOptions opts = new SuppressionCommandOptions
            {
                Path = basePath,
                SarifInput = sarifPath,
                ApplyAllSuppression = true,
                Reviewer = reviewerName,
                Duration = duration
            };
            DateTime expectedExpiration = DateTime.Now.AddDays(duration);
            int resultCode = new SuppressionCommand(opts).Run();
            Assert.AreEqual(0, resultCode);
            string[] result = File.ReadAllLines(sourceFile);
            Suppression firstLineSuppression = new Suppression(result[0]);
            Assert.IsTrue(firstLineSuppression.IsInEffect);
            Assert.AreEqual("DS126858", firstLineSuppression.GetSuppressedIds.First());
            Assert.AreEqual(reviewerName, firstLineSuppression.Reviewer);
            Assert.AreEqual(expectedExpiration.Date, firstLineSuppression.ExpirationDate);
            Suppression secondLineSuppression = new Suppression(result[1]);
            Assert.IsTrue(secondLineSuppression.IsInEffect);
            Assert.AreEqual("DS137138", secondLineSuppression.GetSuppressedIds.First());
            Assert.AreEqual(reviewerName, secondLineSuppression.Reviewer);
            Assert.AreEqual(expectedExpiration.Date, secondLineSuppression.ExpirationDate);
        }

        [DataTestMethod]
        [DataRow("")]
        [DataRow("Contoso")]
        public void ExecuteSuppressionsWithReviewerName(string reviewerName)
        {
            (string basePath, string sourceFile, string sarifPath) = runAnalysis(@"MD5;
            http://contoso.com", "c");

            SuppressionCommandOptions opts = new SuppressionCommandOptions
            {
                Path = basePath,
                SarifInput = sarifPath,
                ApplyAllSuppression = true,
                Reviewer = reviewerName
            };

            int resultCode = new SuppressionCommand(opts).Run();
            Assert.AreEqual(0, resultCode);
            string[] result = File.ReadAllLines(sourceFile);
            Suppression firstLineSuppression = new Suppression(result[0]);
            Assert.IsTrue(firstLineSuppression.IsInEffect);
            Assert.AreEqual("DS126858", firstLineSuppression.GetSuppressedIds.First());
            Assert.AreEqual(reviewerName, firstLineSuppression.Reviewer);
            Suppression secondLineSuppression = new Suppression(result[1]);
            Assert.IsTrue(secondLineSuppression.IsInEffect);
            Assert.AreEqual("DS137138", secondLineSuppression.GetSuppressedIds.First());
            Assert.AreEqual(reviewerName, secondLineSuppression.Reviewer);
        }

        [DataTestMethod]
        [DataRow(true)]
        [DataRow(false)]
        public void ExecuteSuppressions(bool preferMultiLine)
        {
            (string basePath, string sourceFile, string sarifPath) = runAnalysis(@"MD5;
            http://contoso.com", "c");

            SuppressionCommandOptions opts = new SuppressionCommandOptions
            {
                Path = basePath,
                SarifInput = sarifPath,
                ApplyAllSuppression = true,
                PreferMultiline = preferMultiLine
            };

            int resultCode = new SuppressionCommand(opts).Run();
            Assert.AreEqual(0, resultCode);
            string[] result = File.ReadAllLines(sourceFile);
            Suppression firstLineSuppression = new Suppression(result[0]);
            Assert.IsTrue(firstLineSuppression.IsInEffect);
            Assert.AreEqual("DS126858", firstLineSuppression.GetSuppressedIds.First());
            Suppression secondLineSuppression = new Suppression(result[1]);
            Assert.IsTrue(secondLineSuppression.IsInEffect);
            Assert.AreEqual("DS137138", secondLineSuppression.GetSuppressedIds.First());
        }

        [DataTestMethod]
        [DataRow(true)]
        [DataRow(false)]
        public void ExecuteMultipleSuppressionsInOneLine(bool preferMultiLineFormat)
        {
            (string basePath, string sourceFile, string sarifPath) = runAnalysis(@"MD5;http://contoso.com", "c");

            SuppressionCommandOptions opts = new SuppressionCommandOptions
            {
                Path = basePath,
                SarifInput = sarifPath,
                ApplyAllSuppression = true,
                PreferMultiline = preferMultiLineFormat
            };

            int resultCode = new SuppressionCommand(opts).Run();
            Assert.AreEqual(0, resultCode);
            string[] result = File.ReadAllLines(sourceFile);
            Suppression firstLineSuppression = new Suppression(result[0]);
            Assert.IsTrue(firstLineSuppression.IsInEffect);
            Assert.AreEqual("DS137138", firstLineSuppression.GetSuppressedIds[0]);
            Assert.AreEqual("DS126858", firstLineSuppression.GetSuppressedIds[1]);
        }

        [DataTestMethod]
        [DataRow(true)]
        [DataRow(false)]
        public void ExecuteSuppressionsOnlyForSpecifiedRules(bool preferMultiLineFormat)
        {
            (string basePath, string sourceFile, string sarifPath) = runAnalysis(@"MD5;http://contoso.com", "c");

            SuppressionCommandOptions opts = new SuppressionCommandOptions
            {
                Path = basePath,
                SarifInput = sarifPath,
                ApplyAllSuppression = true,
                PreferMultiline = preferMultiLineFormat,
                RulesToApplyFrom = new string[] { "DS137138" }
            };

            int resultCode = new SuppressionCommand(opts).Run();
            Assert.AreEqual(0, resultCode);
            string[] result = File.ReadAllLines(sourceFile);
            Suppression firstLineSuppression = new Suppression(result[0]);
            Assert.IsTrue(firstLineSuppression.IsInEffect);
            Assert.AreEqual("DS137138", firstLineSuppression.GetSuppressedIds[0]);
            Assert.AreEqual(1, firstLineSuppression.GetSuppressedIds.Length);
        }

        [DataTestMethod]
        [DataRow(true)]
        [DataRow(false)]
        public void ExecuteSuppressionsWithExpiration(bool preferMultiLineFormat)
        {
            (string basePath, string sourceFile, string sarifPath) = runAnalysis(@"MD5;http://contoso.com", "c");

            SuppressionCommandOptions opts = new SuppressionCommandOptions
            {
                Path = basePath,
                SarifInput = sarifPath,
                ApplyAllSuppression = true,
                PreferMultiline = preferMultiLineFormat,
                Duration = 30
            };
            DateTime expectedExpiration = DateTime.Now.AddDays(30);
            int resultCode = new SuppressionCommand(opts).Run();
            Assert.AreEqual(0, resultCode);
            string[] result = File.ReadAllLines(sourceFile);
            Suppression firstLineSuppression = new Suppression(result[0]);
            Assert.IsTrue(firstLineSuppression.IsInEffect);
            Assert.AreEqual("DS137138", firstLineSuppression.GetSuppressedIds[0]);
            Assert.AreEqual("DS126858", firstLineSuppression.GetSuppressedIds[1]);
            Assert.AreEqual(expectedExpiration.Date, firstLineSuppression.ExpirationDate);
        }

        [DataTestMethod]
        [DataRow(true)]
        [DataRow(false)]
        public void NotExecuteSuppressions(bool preferMultiLine)
        {
            (string basePath, string sourceFile, string sarifPath) = runAnalysis(@"MD5;
            http://", "c");

            SuppressionCommandOptions opts = new SuppressionCommandOptions
            {
                Path = basePath,
                SarifInput = sarifPath,
                PreferMultiline = preferMultiLine
            };

            int resultCode = new SuppressionCommand(opts).Run();
            Assert.AreEqual((int)ExitCode.CriticalError, resultCode);
            string result = File.ReadAllText(sourceFile);
            Assert.IsFalse(result.Contains("DevSkim: ignore"));
        }

        [TestMethod]
        public void ExecuteDryRun()
        {
            (string basePath, string sourceFile, string sarifPath) = runAnalysis(@"MD5;
            http://", "c");

            SuppressionCommandOptions opts = new SuppressionCommandOptions
            {
                Path = basePath,
                SarifInput = sarifPath,
                ApplyAllSuppression = true,
                DryRun = true,
            };

            int resultCode = new SuppressionCommand(opts).Run();
            string result = File.ReadAllText(sourceFile);

            Assert.IsFalse(result.Contains("DevSkim: ignore"));
        }

        [TestMethod]
        public void ExecuteSuppressionsOnSpecificFiles()
        {
            (string basePath, string sourceFile, string sarifPath) = runAnalysis(@"MD5;
            http://", "c");

            SuppressionCommandOptions opts = new SuppressionCommandOptions
            {
                Path = basePath,
                SarifInput = sarifPath,
                ApplyAllSuppression = true,
                FilesToApplyTo = new string[] { "/tmp/not-existing.c" }
            };

            int resultCode = new SuppressionCommand(opts).Run();
            string result = File.ReadAllText(sourceFile);

            Assert.IsFalse(result.Contains("DevSkim: ignore"));
        }

        [DataTestMethod]
        [DataRow(true)]
        [DataRow(false)]
        public void ExecuteSuppresionsForMultilineFormattedFiles(bool preferMultiLine)
        {
            (string basePath, string sourceFile, string sarifPath) = runAnalysis(@"MD5 \
            Test;
            http://contoso.com", "c");

            SuppressionCommandOptions opts = new SuppressionCommandOptions
            {
                Path = basePath,
                SarifInput = sarifPath,
                ApplyAllSuppression = true,
                PreferMultiline = preferMultiLine
            };

            int resultCode = new SuppressionCommand(opts).Run();
            Assert.AreEqual(0, resultCode);
            string[] result = File.ReadAllLines(sourceFile);
            Suppression firstLineSuppression = new Suppression(result[0]);
            Assert.IsTrue(firstLineSuppression.IsInEffect);
            Assert.AreEqual("DS126858", firstLineSuppression.GetSuppressedIds.First());
            Suppression secondLineSuppression = new Suppression(result[2]);
            Assert.IsTrue(secondLineSuppression.IsInEffect);
            Assert.AreEqual("DS137138", secondLineSuppression.GetSuppressedIds.First());
        }

        private (string basePath, string sourceFile, string sarifPath) runAnalysis(string content, string ext)
        {
            string tempFileName = $"{Path.GetTempFileName()}.{ext}";
            string outFileName = Path.GetTempFileName();
            File.Delete(outFileName);

            string basePath = Path.GetTempPath();
            string oneUpPath = Directory.GetParent(basePath).FullName;
            using FileStream file = File.Open(tempFileName, FileMode.Create);
            file.Write(Encoding.UTF8.GetBytes(content));
            file.Close();

            AnalyzeCommandOptions opts = new AnalyzeCommandOptions()
            {
                Path = tempFileName,
                OutputFile = outFileName,
                OutputFileFormat = "sarif",
                BasePath = basePath
            };

            new AnalyzeCommand(opts).Run();
            return (basePath, tempFileName, Path.Combine(basePath, outFileName));
        }
    }
}