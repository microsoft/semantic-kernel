using System.Text.Json;
using Microsoft.ApplicationInspector.RulesEngine;
using Microsoft.DevSkim.CLI.Commands;
using Microsoft.DevSkim.CLI.Options;

namespace Microsoft.DevSkim.Tests;

[TestClass]
public class OptionsTests
{
    [TestMethod]
    public void TestParsingJsonOptions()
    {
        var ruleIdToIgnore = "JsonOptionParseTest";
        // Create a SerializedAnalyzeCommandOptions object
        var serializedOpts = new SerializedAnalyzeCommandOptions()
        {
            Severities = new[] { Severity.Critical | Severity.Important },
            ExitCodeIsNumIssues = true,
            LanguageRuleIgnoreMap = new Dictionary<string, List<string>>()
            {
                { "csharp", new List<string>() { ruleIdToIgnore } }
            }
        };
        var serializedOpts2 = new SerializedAnalyzeCommandOptions()
        {
            Severities = new[] { Severity.Critical | Severity.Important },
            ExitCodeIsNumIssues = true,
            Globs = new List<string>() {"*.js"}
        };
        // Serialize it to a file
        var testContent = "Hello World";
        var testRule =
@"[
    {
        ""name"": ""Weak/Broken Hash Algorithm"",
        ""id"": ""JsonOptionParseTest"",
        ""description"": ""A test that finds hello"",
        ""tags"": [
            ""Tests.JsonOptionsTest""
        ],
        ""severity"": ""critical"",
        ""patterns"": [
            {
                ""pattern"": ""Hello"",
                ""type"": ""regex"",
                ""scopes"": [
                    ""code""
                ]
            }
        ]
    },
    {
        ""name"": ""Weak/Broken Hash Algorithm"",
        ""id"": ""JsonOptionParseTest2"",
        ""description"": ""A test that finds hello and isn't ignored"",
        ""tags"": [
            ""Tests.JsonOptionsTest""
        ],
        ""severity"": ""important"",
        ""patterns"": [
            {
                ""pattern"": ""World"",
                ""type"": ""regex"",
                ""scopes"": [
                    ""code""
                ]
            }
        ]
    }
]";
        var rulesPath = PathHelper.GetRandomTempFile("json");
        var serializedJsonPath = PathHelper.GetRandomTempFile("json");
        var serializedJsonPath2 = PathHelper.GetRandomTempFile("json");
        var csharpTestPath = PathHelper.GetRandomTempFile("cs");
        var jsTestPath = PathHelper.GetRandomTempFile("js");
        {
            using var serializedJsonStream = File.Create(serializedJsonPath);
            JsonSerializer.Serialize(serializedJsonStream, serializedOpts, new JsonSerializerOptions() { });
            using var serializedJsonStream2 = File.Create(serializedJsonPath2);
            JsonSerializer.Serialize(serializedJsonStream2, serializedOpts2, new JsonSerializerOptions() { });
            using var csharpStream = File.Create(csharpTestPath);
            JsonSerializer.Serialize(csharpStream, testContent);
            using var jsStream = File.Create(jsTestPath);
            JsonSerializer.Serialize(jsStream, testContent);
            File.WriteAllText(rulesPath, testRule);
        }

        // Create an AnalyzeCommandOptions object that references the path to the file which ignores a specific rule
        var analyzeOpts = new AnalyzeCommandOptions()
        {
            Path = csharpTestPath,
            Rules = new[] { rulesPath },
            PathToOptionsJson = serializedJsonPath
        };

        var analyzerWithSerialized = new AnalyzeCommand(analyzeOpts);
        // We set exit code is num issues so this should be 1, from the 1 rule that isn't ignored
        Assert.AreEqual(1, analyzerWithSerialized.Run());
        // Create an AnalyzeCommandOptions object that references the path to the file which ignores a specific rule
        analyzeOpts = new AnalyzeCommandOptions()
        {
            Path = csharpTestPath,
            Rules = new[] { rulesPath },
            ExitCodeIsNumIssues = true,
            Severities = new Severity[] { Severity.Critical }
        };
        analyzerWithSerialized = new AnalyzeCommand(analyzeOpts);
        // This should be 1, because we haven't expressed the json option argument which sets the severity
        Assert.AreEqual(1, analyzerWithSerialized.Run());

        // Try the js which it should find both
        analyzeOpts = new AnalyzeCommandOptions()
        {
            Path = jsTestPath,
            Rules = new[] { rulesPath },
            PathToOptionsJson = serializedJsonPath
        };
        analyzerWithSerialized = new AnalyzeCommand(analyzeOpts);
        // This should be 2, because 2 rules aren't ignored
        Assert.AreEqual(2, analyzerWithSerialized.Run());
        // Try the js which it should find both
        analyzeOpts = new AnalyzeCommandOptions()
        {
            Path = jsTestPath,
            Rules = new[] { rulesPath },
            PathToOptionsJson = serializedJsonPath,
            Severities = new[] { Severity.Critical }
        };
        analyzerWithSerialized = new AnalyzeCommand(analyzeOpts);
        // This should be 1, because only one rule has severity critical
        Assert.AreEqual(1, analyzerWithSerialized.Run());
        // Test that an option explicitly set overrides an option set in the json
        
        // set of options to test enumerable parsing
        analyzeOpts = new AnalyzeCommandOptions()
        {
            Path = csharpTestPath,
            Rules = new[] { rulesPath },
            PathToOptionsJson = serializedJsonPath2
        };
        analyzerWithSerialized = new AnalyzeCommand(analyzeOpts);
        // This should be 2, because the globs dont exclude cs files
        Assert.AreEqual(2, analyzerWithSerialized.Run());
        // set of options to test enumerable parsing
        analyzeOpts = new AnalyzeCommandOptions()
        {
            Path = jsTestPath,
            Rules = new[] { rulesPath },
            PathToOptionsJson = serializedJsonPath2
        };
        analyzerWithSerialized = new AnalyzeCommand(analyzeOpts);
        // This should be 0, because the globs exclude js files
        Assert.AreEqual(0, analyzerWithSerialized.Run());
    }
}