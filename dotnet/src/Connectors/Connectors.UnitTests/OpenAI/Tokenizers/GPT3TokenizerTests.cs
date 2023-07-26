// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text;
using System.Text.Json;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.Tokenizers;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.Connectors.UnitTests.OpenAI.Tokenizers;

#pragma warning disable CA5394
public class GPT3TokenizerTests
{
    private readonly ITestOutputHelper _logger;

    public GPT3TokenizerTests(ITestOutputHelper logger)
    {
        this._logger = logger;
    }

    // ReSharper disable StringLiteralTypo
    [Theory]
    [InlineData("", 0)]
    [InlineData("a", 1)]
    [InlineData("abbccd", 3)]
    [InlineData("ab bc cd", 3)]
    [InlineData("ab + bc + cd = 10.", 8)]
    [InlineData("Array.prototype.slice()", 6)]
    [InlineData("const animals = ['ant', 'bison', 'camel', 'duck', 'elephant'];", 23)]
    [InlineData(" c o n s t   a n i m a l s   =   [ ' a n t ' ,   ' b i s o n ' ,   ' c a m e l ' ,   ' d u c k ' ,   ' e l e p h a n t ' ] ; ", 70)]
    [InlineData("Many words map to one token, but some don't: indivisible.", 16)]
    [InlineData("Unicode characters like emojis may be split into many tokens containing the underlying bytes: 🤚🏾", 25)]
    [InlineData("Sequences of characters commonly found next to each other may be grouped together: 1234567890", 19)]
    [InlineData("ἀμφὶ Ποσειδάωτα, μέγαν θεόν, ἄρχομ᾽ ἀείδειν,", 58)]
    [InlineData("This is a test 𝓣𝓱𝓲𝓼 𝓲𝓼 𝓪 𝓽𝓮𝓼𝓽", 41)]
    [InlineData("This.▶︎ is🎶 a😀 test🐼", 17)]
    [InlineData(
        "在计算机编程中，单元测试（英語：Unit Testing）又称为模块测试 [來源請求] ，是针对程序模块（软件设计的最小单位）来进行正确性检验的测试工作。程序单元是应用的最小可测试部件。在过程化编程中，一个单元就是单个程序、函数、过程等；对于面向对象编程，最小单元就是方法，包括基类（超类）、抽象类、或者派生类（子类）中的方法。 ",
        334)]
    [InlineData(@"En programación, una prueba unitaria o test unitario (del inglés: unit test)
es una forma efectiva de comprobar el correcto funcionamiento de las unidades individuales
más pequeñas de los programas informáticos", 68)]
    // ReSharper restore StringLiteralTypo
    public void ItReturnsTheCorrectNumberOfTokens(string text, int tokenCount)
    {
        // Act-Assert
        Assert.Equal(tokenCount, GPT3Tokenizer.Encode(text).Count);
        Assert.Equal(tokenCount, GPT3Tokenizer.Encode(new StringBuilder(text)).Count);
        Assert.Equal(tokenCount, GPT3Tokenizer.Encode(text.ToArray()).Count);
        Assert.Equal(tokenCount, GPT3Tokenizer.Encode(text.ToCharArray()).Count);
        Assert.Equal(tokenCount, GPT3Tokenizer.Encode(text.ToCharArray().ToList()).Count);
    }

    // TODO: check actual token IDs// ReSharper disable StringLiteralTypo
    [Theory]
    [InlineData("", "[]")]
    [InlineData("a", "[64]")]
    [InlineData("abbccd", "[6485, 535, 67]")]
    [InlineData("ab bc cd", "[397, 47125, 22927]")]
    [InlineData("January 1st, 2000", "[21339, 352, 301, 11, 4751]")]
    [InlineData("ab + bc + cd = 10.", "[397, 1343, 47125, 1343, 22927, 796, 838, 13]")]
    [InlineData("Array.prototype.slice()", "[19182, 13, 38124, 13, 48369, 3419]")]
    [InlineData("const animals = ['ant', 'bison', 'camel', 'duck', 'elephant'];",
        "[9979,4695,796,37250,415,3256,705,65,1653,3256,705,66,17983,3256,705,646,694,3256,705,11129,33959,6,11208]")]
    [InlineData(" c o n s t   a n i m a l s   =   [ ' a n t ' ,   ' b i s o n ' ,   ' c a m e l ' ,   ' d u c k ' ,   ' e l e p h a n t ' ] ; ",
        "[269,267,299,264,256,220,220,257,299,1312,285,257,300,264,220,220,796,220,220,685,705,257,299,256,705,837,220,220,705,275,1312,264,267,299,705,837,220,220,705,269,257,285,304,300,705,837,220,220,705,288,334,269,479,705,837,220,220,705,304,300,304,279,289,257,299,256,705,2361,2162,220]")]
    [InlineData("This is a test 𝓣𝓱𝓲𝓼 𝓲𝓼 𝓪 𝓽𝓮𝓼𝓽",
        "[1212,318,257,1332,220,47728,241,96,47728,241,109,47728,241,110,47728,241,120,220,47728,241,110,47728,241,120,220,47728,241,103,220,47728,241,121,47728,241,106,47728,241,120,47728,241,121]")]
    [InlineData("This.▶︎ is🎶 a😀 test🐼", "[1212,13,5008,114,35266,236,318,8582,236,114,257,47249,222,1332,8582,238,120]")]
    [InlineData("Many words map to one token, but some don't: indivisible.", "[7085,2456,3975,284,530,11241,11,475,617,836,470,25,773,452,12843,13]")]
    [InlineData("Unicode characters like emojis may be split into many tokens containing the underlying bytes: 🤚🏾",
        "[3118,291,1098,3435,588,795,13210,271,743,307,6626,656,867,16326,7268,262,10238,9881,25,12520,97,248,8582,237,122]")]
    [InlineData("Sequences of characters commonly found next to each other may be grouped together: 1234567890",
        "[44015,3007,286,3435,8811,1043,1306,284,1123,584,743,307,32824,1978,25,17031,2231,30924,3829]")]
    [InlineData("ἀμφὶ Ποσειδάωτα, μέγαν θεόν, ἄρχομ᾽ ἀείδειν,",
        "[157,120,222,34703,139,228,45495,114,7377,254,26517,38392,30950,29945,138,112,138,105,49535,32830,17394,11,18919,138,255,42063,17394,26180,7377,116,30950,139,234,26180,11,28053,120,226,33643,139,229,26517,34703,157,122,121,28053,120,222,30950,138,107,138,112,30950,29945,26180,11]")]
    // ReSharper restore StringLiteralTypo
    public void ItReturnsTheCorrectTokens(string text, string tokens)
    {
        // Arrange
        List<int> expectedTokens = JsonSerializer.Deserialize<List<int>>(tokens)!;

        // Act
        List<int> actualTokens = GPT3Tokenizer.Encode(text);

        // Assert
        Assert.Equal(expectedTokens.Count, actualTokens.Count);
        Assert.Equal(tokens.Replace(" ", "", StringComparison.OrdinalIgnoreCase),
            JsonSerializer.Serialize(actualTokens).Replace(" ", "", StringComparison.OrdinalIgnoreCase));
    }

    [Fact]
    // ReSharper disable StringLiteralTypo
    public void ItDoesntTimeOutForABigText()
    {
        // Arrange
        const int OneMb = 1000 * 1000;
        var watch = new Stopwatch();
        Random rnd = new();
        StringBuilder text = new();
        watch.Start();
        var count = 0;
        while (text.Length < OneMb)
        {
            text.Append(GenerateWord(rnd, count++));
        }

        watch.Stop();
        this._logger.WriteLine($"Text size: {text.Length}. Text generated in: {watch.ElapsedMilliseconds} msecs.");

        // Act + Assert no exception occurs
        watch.Restart();
        GPT3Tokenizer.Encode(text);
        watch.Stop();
        this._logger.WriteLine($"Text size: {text.Length}. Text tokenized in: {watch.ElapsedMilliseconds} msecs.");
    }

    // Try to generate some random text to reduce the tokenizer cache hits.
    private static string GenerateWord(Random rnd, int count)
    {
        string[] group1 = { "test🐼", "bytes", "  ", "- =", "llllllllllllllllllllllllllllllllllll", "%", "This.▶ ", " group ", "ἄρχομ " };
        string[] group2 = { "b", "c", "d", "f", "g", "h", "j", "k", "l", "m", "n", "p", "q", "r", "s", "t", "v", "w", "x", "y", "z", "\n" };
        string[] group3 = { "a", "e", "i", "o", "u", " " };

        var result = new StringBuilder();

        var length = rnd.Next(1, 200);
        if (length <= 2)
        {
            var word1 = group1[rnd.Next(0, group1.Length)];
            var word2 = group1[rnd.Next(0, group1.Length)];
            result.Append(word1);
            result.Append(word2);
        }
        else
        {
            while (result.Length < length)
            {
                result.Append(group2[rnd.Next(0, group2.Length)]);
                result.Append(group3[rnd.Next(0, group3.Length)]);
                result.Append(rnd.Next(0, 2) == 0 ? group2[rnd.Next(0, group2.Length)] : group3[rnd.Next(0, group3.Length)]);
            }
        }

        return $"{result}{count}";
    }
}
#pragma warning restore CA5394
