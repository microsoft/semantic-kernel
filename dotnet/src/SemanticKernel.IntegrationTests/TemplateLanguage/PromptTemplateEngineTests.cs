// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.TemplateEngine;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.TemplateLanguage;

#pragma warning disable VSTHRD103 // ok to use WriteLine synchronously
#pragma warning disable CA1849 // ok to use WriteLine synchronously

public sealed class PromptTemplateEngineTests : IDisposable
{
    public PromptTemplateEngineTests(ITestOutputHelper output)
    {
        this._logger = new RedirectOutput(output);
        this._target = new PromptTemplateEngine();
    }

    [Fact]
    public async Task ItSupportsVariablesAsync()
    {
        // Arrange
        const string input = "template tests";
        const string winner = "SK";
        const string template = "And the winner\n of {{$input}} \nis: {{  $winner }}!";

        var kernel = Kernel.Builder.Build();
        var context = kernel.CreateNewContext();
        context["input"] = input;
        context["winner"] = winner;

        // Act
        var result = await this._target.RenderAsync(template, context);

        // Assert
        var expected = template
            .Replace("{{$input}}", input, StringComparison.OrdinalIgnoreCase)
            .Replace("{{  $winner }}", winner, StringComparison.OrdinalIgnoreCase);
        Assert.Equal(expected, result);
    }

    [Fact]
    public async Task ItSupportsValuesAsync()
    {
        // Arrange
        const string template = "And the winner\n of {{'template\ntests'}} \nis: {{  \"SK\" }}!";
        const string expected = "And the winner\n of template\ntests \nis: SK!";

        var kernel = Kernel.Builder.Build();
        var context = kernel.CreateNewContext();

        // Act
        var result = await this._target.RenderAsync(template, context);

        // Assert
        Assert.Equal(expected, result);
    }

    [Fact]
    public async Task ItAllowsToPassVariablesToFunctionsAsync()
    {
        // Arrange
        const string template = "== {{my.check123 $call}} ==";
        var kernel = Kernel.Builder.Build();
        kernel.ImportSkill(new MySkill(), "my");
        var context = kernel.CreateNewContext();
        context["call"] = "123";

        // Act
        var result = await this._target.RenderAsync(template, context);

        // Assert
        Assert.Equal("== 123 ok ==", result);
    }

    [Fact]
    public async Task ItAllowsToPassValuesToFunctionsAsync()
    {
        // Arrange
        const string template = "== {{my.check123 '234'}} ==";
        var kernel = Kernel.Builder.Build();
        kernel.ImportSkill(new MySkill(), "my");
        var context = kernel.CreateNewContext();

        // Act
        var result = await this._target.RenderAsync(template, context);

        // Assert
        Assert.Equal("== 234 != 123 ==", result);
    }

    [Fact]
    public async Task ItAllowsToPassEscapedValues1ToFunctionsAsync()
    {
        // Arrange
        const char ESC = '\\';
        string template = "== {{my.check123 'a" + ESC + "'b'}} ==";
        var kernel = Kernel.Builder.Build();
        kernel.ImportSkill(new MySkill(), "my");
        var context = kernel.CreateNewContext();

        // Act
        var result = await this._target.RenderAsync(template, context);

        // Assert
        Assert.Equal("== a'b != 123 ==", result);
    }

    [Fact]
    public async Task ItAllowsToPassEscapedValues2ToFunctionsAsync()
    {
        // Arrange
        const char ESC = '\\';
        string template = "== {{my.check123 \"a" + ESC + "\"b\"}} ==";
        var kernel = Kernel.Builder.Build();
        kernel.ImportSkill(new MySkill(), "my");
        var context = kernel.CreateNewContext();

        // Act
        var result = await this._target.RenderAsync(template, context);

        // Assert
        Assert.Equal("== a\"b != 123 ==", result);
    }

    [Theory]
    [MemberData(nameof(GetTemplateLanguageTests))]
    public async Task ItHandleEdgeCasesAsync(string template, string expectedResult)
    {
        // Arrange
        var kernel = Kernel.Builder.Build();
        kernel.ImportSkill(new MySkill());

        // Act
        this._logger.WriteLine("template: " + template);
        this._logger.WriteLine("expected: " + expectedResult);
        if (expectedResult.StartsWith("ERROR", StringComparison.OrdinalIgnoreCase))
        {
            await Assert.ThrowsAsync<TemplateException>(
                async () => await this._target.RenderAsync(template, kernel.CreateNewContext()));
        }
        else
        {
            var result = await this._target.RenderAsync(template, kernel.CreateNewContext());
            this._logger.WriteLine("  result: " + result);

            // Assert
            Assert.Equal(expectedResult, result);
        }
    }

    public static IEnumerable<object[]> GetTemplateLanguageTests()
    {
        return GetTestData("TemplateLanguage/tests.txt");
    }

    public class MySkill
    {
        [SKFunction("This is a test")]
        [SKFunctionName("check123")]
        public string MyFunction(string input)
        {
            return input == "123" ? "123 ok" : input + " != 123";
        }

        [SKFunction("This is a test")]
        [SKFunctionName("asis")]
        public string MyFunction2(string input)
        {
            return input;
        }
    }

    #region internals

    private readonly RedirectOutput _logger;
    private readonly PromptTemplateEngine _target;

    private static IEnumerable<string[]> GetTestData(string file)
    {
        if (!File.Exists(file)) { Assert.Fail("File not found: " + file); }

        var content = File.ReadLines(file);
        var key = string.Empty;
        foreach (string value in content)
        {
            if (string.IsNullOrEmpty(value) || value.StartsWith('#')) { continue; }

            if (string.IsNullOrEmpty(key))
            {
                key = value;
            }
            else
            {
                yield return new string[] { key, value };
                key = string.Empty;
            }
        }
    }

    public void Dispose()
    {
        this._logger.Dispose();
    }

    #endregion
}

#pragma warning restore VSTHRD103
#pragma warning restore CA1849
