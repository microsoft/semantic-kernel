namespace Microsoft.DevSkim.Tests;

[TestClass]
public class DefaultRulesTests
{
    private static string _guidanceDirectory = string.Empty;

    [ClassInitialize]
    public static void ClassInitialize(TestContext testContext)
    {
        string directory = Directory.GetCurrentDirectory();

        /* Given a directory, like: "C:\src\DevSkim\DevSkim-DotNet\Microsoft.DevSkim.Tests\bin\Debug\net8.0"     - local dev
         * OR                       "/mnt/vss/_work/1/s/DevSkim-DotNet/Microsoft.DevSkim.Tests/bin/Debug/net8.0" - CI for DevSkim CLI
         * we want to find:         "C:\src\DevSkim\guidance"
         * 
         * so we look for DevSkim-DotNet and then go up one more level to find guidance.
         */

        var currentDirInfo = new DirectoryInfo(directory);
        while (currentDirInfo != null && currentDirInfo.Name != "DevSkim-DotNet")
        {
            currentDirInfo = currentDirInfo.Parent;
        }

        currentDirInfo = currentDirInfo?.Parent;

        if (currentDirInfo == null)
        {
            string message = $"Could not find DevSkim-DotNet directory from: {directory}.";
            throw new Exception(message);
        }

        string guidanceDir = Path.Combine(currentDirInfo.FullName, "guidance");
        if (!Directory.Exists(guidanceDir))
        {
            throw new Exception($"Guidance directory {guidanceDir} does not exist.");
        }

        _guidanceDirectory = guidanceDir;
    }

    [TestMethod]
    public void ValidateDefaultRules()
    {
        DevSkimRuleSet devSkimRuleSet = DevSkimRuleSet.GetDefaultRuleSet();
        Assert.AreNotEqual(0, devSkimRuleSet.Count());
        var validator = new DevSkimRuleVerifier(new DevSkimRuleVerifierOptions()
        {
            LanguageSpecs = DevSkimLanguages.LoadEmbedded()
        });
        DevSkimRulesVerificationResult result = validator.Verify(devSkimRuleSet);
        foreach (ApplicationInspector.RulesEngine.RuleStatus status in result.Errors)
        {
            foreach (string error in status.Errors)
            {
                Console.WriteLine(error);
            }
        }

        Console.WriteLine("{0} of {1} rules have positive self-tests.", result.DevSkimRuleStatuses.Count(x => x.HasPositiveSelfTests), result.DevSkimRuleStatuses.Count());
        Console.WriteLine("{0} of {1} rules have negative self-tests.", result.DevSkimRuleStatuses.Count(x => x.HasNegativeSelfTests), result.DevSkimRuleStatuses.Count());

        Assert.IsTrue(result.Verified);
        Assert.IsFalse(result.DevSkimRuleStatuses.Any(x => x.Errors.Any()));
    }

    [TestMethod]
    public void DenamespacedRule()
    {
        string content = @"<?xml version=""1.0"" encoding=""UTF-8""?>
<project xmlns=""http://maven.apache.org/POM/4.0.0"" xmlns:xsi=""http://www.w3.org/2001/XMLSchema-instance"" xsi:schemaLocation=""http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd"">
  <modelVersion>4.0.0</modelVersion>

  <groupId>xxx</groupId>
  <artifactId>xxx</artifactId>
  <version>0.1.0-SNAPSHOT</version>
  <packaging>pom</packaging>

  <name>${project.groupId}:${project.artifactId}</name>
  <description />

  <properties>
    <java.version>17</java.version>
  </properties>

</project>";
        string rule = @"[{
  ""name"": ""Source code: Java 17"",
  ""id"": ""CODEJAVA000000"",
  ""description"": ""Java 17 maven configuration"",
  ""applies_to"": [
    ""xml""
  ],
  ""tags"": [
    ""Code.Java.17""
  ],
  ""severity"": ""critical"",
  ""patterns"": [
    {
      ""pattern"": ""17"",
      ""xpaths"" : [""/*[local-name(.)='project']/*[local-name(.)='properties']/*[local-name(.)='java.version']""],
      ""type"": ""regex"",
      ""scopes"": [
        ""code""
      ],
      ""modifiers"": [
        ""i""
      ],
      ""confidence"": ""high""
    }
  ]
}]";
        DevSkimRuleSet devSkimRuleSet = new DevSkimRuleSet();
        devSkimRuleSet.AddString(rule, "testRules");
        DevSkimRuleProcessor analyzer = new DevSkimRuleProcessor(devSkimRuleSet, new DevSkimRuleProcessorOptions());
        IEnumerable<Issue> analysis = analyzer.Analyze(content, "thing.xml");
        Assert.AreEqual(1, analysis.Count());
    }

    public static IEnumerable<object[]> DefaultRules
    {
        get
        {
            DevSkimRuleSet devSkimRuleSet = DevSkimRuleSet.GetDefaultRuleSet();
            foreach (DevSkimRule rule in devSkimRuleSet)
            {
                yield return new object[] { rule };
            }
        }
    }

    [TestMethod]
    [DynamicData(nameof(DefaultRules))]
    public void Rule_guidance_file_should_be_specified_and_exist(DevSkimRule rule)
    {
        if (rule.Disabled)
        {
            Assert.Inconclusive("Rule is disabled.");
        }

        if (string.IsNullOrEmpty(rule.RuleInfo))
        {
            Assert.Fail("Rule does not specify guidance file.");
        }

        string guidanceFile = Path.Combine(_guidanceDirectory, rule.RuleInfo);
        Assert.IsTrue(File.Exists(guidanceFile), $"Guidance file {guidanceFile} does not exist.");
    }

    [TestMethod]
    [DynamicData(nameof(DefaultRules))]
    public void Rule_guidance_should_be_complete(DevSkimRule rule)
    {
        if (rule.Disabled)
        {
            Assert.Inconclusive("Rule is disabled.");
        }

        if(string.IsNullOrEmpty(rule.RuleInfo))
        {
            Assert.Inconclusive("Rule does not specify guidance file.");
        }

        string guidanceFile = Path.Combine(_guidanceDirectory, rule.RuleInfo);
        if(!File.Exists(guidanceFile))
        {
            Assert.Inconclusive("Guidance file does not exist");
        }

        string guidance = File.ReadAllText(guidanceFile);
        bool hasContent = !string.IsNullOrEmpty(guidance);
        Assert.IsTrue(hasContent, $"Guidance file {guidanceFile} is empty.");

        if (rule.Id != "DS176209" && // "Suspicious comment" - a TODO comment
            (guidance.Contains("TODO", StringComparison.OrdinalIgnoreCase)
            || guidance.Contains("TO DO", StringComparison.OrdinalIgnoreCase)))
        {
            Assert.Fail($"Guidance file {guidanceFile} contains TODO.");
        }
    }
}