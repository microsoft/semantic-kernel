// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using Microsoft.ML.Tokenizers;
using Microsoft.SemanticKernel.Text;
using Xunit;
using static Microsoft.SemanticKernel.Text.TextChunker;

namespace SemanticKernel.UnitTests.Text;

public sealed class TextChunkerInternationalTests
{
    public sealed class StatefulTokenCounter
    {
        private readonly Dictionary<string, int> _callStats = [];
        private readonly Tokenizer _tokenizer = TiktokenTokenizer.CreateForModel("gpt-4");

        public int Count(string input)
        {
            this.CallCount++;
            this._callStats[input] = this._callStats.TryGetValue(input, out int value) ? value + 1 : 1;
            return this._tokenizer.CountTokens(input);
        }

        public int CallCount { get; private set; } = 0;
    }

    private static TokenCounter StatelessTokenCounter => (string input) =>
    {
        var tokenizer = TiktokenTokenizer.CreateForModel("gpt-4");
        return tokenizer.CountTokens(input);
    };

    [Fact]
    public void TokenCounterCountStateful()
    {
        var counter = new StatefulTokenCounter();
        var lines = TextChunker.SplitPlainTextLines("This is a test", 40, counter.Count);
    }

    [Fact]
    public void TokenCounterCountStateless()
    {
        var counter = new StatefulTokenCounter();
        var lines = TextChunker.SplitPlainTextLines("This is a test", 40, StatelessTokenCounter);
    }

    [Fact]
    public void CanSplitParagraphsWithIdeographicPunctuationAndGptTokenCounter()
    {
        var counter = new StatefulTokenCounter();
        const string Input = "田中の猫はかわいいですね。日本語上手。";
        var expected = new[]
        {
            "田中の猫はかわいいですね。",
            "日本語上手。"
        };

        var result = TextChunker.SplitPlainTextLines(Input, 16, counter.Count);

        Assert.Equal(expected, result);
    }

    /**
     * The following stories were generated with GPT-4 with the prompt
     * "Generate a short story about a mouse that goes on an adventure to a big city."
     */
    [Theory]
    [InlineData("English", "The little mouse lived in a peaceful small village. He always saw the same scenery and interacted with the same friends. One day, he decided to venture to the big city. Carrying a small backpack, he boarded the train.\n\nThe city was a world full of wonders for the little mouse. Tall buildings, bright neon signs, and the hustle and bustle of people. His eyes sparkled as he wandered around. However, he needed some time to get used to this big world.\n\nOne day, the mouse met a big rat in the park. The big rat said to him, “Did you come from a small village? The city can be tough at times, but there are new friends and exciting adventures waiting for you.”\n\nThe mouse nodded with a smile. He decided to find new friends in the city and expand his little world. ")]
    [InlineData("Japanese", "もぐらは小さな町で暮らしていました。彼はいつも同じ風景と同じ友達に囲まれていました。ある日、彼は大都市への冒険を決意しました。彼は小さなかばんを持ち、列車に乗り込みました。" +
            "大都市はもぐらにとって驚きの連続でした。高いビル、明るいネオンサイン、人々の喧騒。彼は目を輝かせて歩き回りました。しかし、彼はもう少し大きな世界に慣れる必要がありました。" +
            "ある日、もぐらは公園で大きなネズミに出会いました。ネズミはもぐらに言いました。「小さな町から来たの？大都市は時には厳しいけれど、新しい友達と素晴らしい冒険が待っているよ。」" +
            "もぐらは笑顔で頷きました。彼は大都市で新しい友達を見つけ、自分の小さな世界を広げることを決めました。")]
    [InlineData("Korean", "작은 마을에서 살던 쥐는 언젠가 큰 도시로 모험을 떠나기로 결심했습니다. 그는 작은 가방을 메고 기차에 탔습니다.\n\n도시는 그에게 놀라움의 연속이었습니다. 높은 빌딩, " +
            "밝은 네온 사인, 사람들의 소음. 그는 눈을 반짝이며 거리를 돌아다녔습니다. 하지만 그는 이 큰 세계에 조금 더 익숙해져야 했습니다.\n\n어느 날, 그는 공원에서 큰 쥐를 만났" +
            "습니다. 큰 쥐는 그에게 말했습니다. \"작은 마을에서 온 거야? 도시는 때로는 힘들지만, 새로운 친구와 멋진 모험이 기다리고 있어.\"\n\n쥐는 미소를 지었습니다. 그는 도시에서" +
            "새로운 친구를 만나고 작은 세계를 넓히기로 결심했습니다.")]
    [InlineData("Arabic", "كان الفأر يعيش في قرية صغيرة. كان يرى نفس المناظر ويتعامل مع نفس الأصدقاء دائمًا. في يوم من الأيام، قرر الفأر أن يغامر ويذهب إلى المدينة الكبيرة. حمل حقيبة صغيرة وركب القطار.\n\nكانت المدينة مليئة بالمفاجآت بالنسبة للفأر. المباني العالية، اللافتات النيون المشرقة، وضجيج الناس. كان يتجول بعيون متلألئة. ومع ذلك، كان عليه أن يتعود على هذا العالم الكبير قليلاً.\n\nفي يوم من الأيام، التقى الفأر بفأر كبير في الحديقة. قال له الفأر الكبير: \"أتيت من قرية صغيرة؟ المدينة قد تكون صعبة في بعض الأحيان، لكن هناك أصدقاء جدد ومغامرات رائعة في انتظارك.")]
    [InlineData("Chinese", "小老鼠住在一个宁静的小村庄里。他总是看着同样的风景，与同样的朋友们相处。有一天，他决定要去大城市冒险。他背着一个小小的背包，坐上了火车。\n\n大城市对小老鼠来说是一个充满惊奇的世界。高楼大厦、明亮的霓虹灯、人们的喧嚣声。他眼睛发亮地四处走动。然而，他需要一点时间来适应这个大世界。\n\n有一天，小老鼠在公园里遇到了一只大老鼠。大老鼠对他说：“你是从小村庄来的吗？大城市有时会很艰难，但也有新朋友和精彩的冒险等着你。”\n\n小老鼠微笑着点了点头。他决定在大城市里寻找新朋友，扩展自己的小小世界。")]
    public void VerifyShortStoryInLanguage(string language, string story)
    {
        var counter = new StatefulTokenCounter();
        var actualResult = TextChunker.SplitPlainTextLines(story, 20, counter.Count);

        Assert.True(counter.CallCount > 0);
        Assert.True(counter.CallCount < story.Length / 2);

        foreach (var line in actualResult)
        {
            Assert.True(counter.Count(line) <= 20);
        }

        var expectedResult = GetLanguageExpectedResult(language);

        Assert.Equal(expectedResult, actualResult);
    }

    #region private

    private static List<string> GetLanguageExpectedResult(string language)
    {
        var fileName = $"TextChunkerInternationalTests.VerifyShortStoryInLanguage_language={language}.txt";
        var filePath = Path.Combine(Directory.GetCurrentDirectory(), "Text", fileName);

        var fileContent = File.ReadAllText(filePath);

        return JsonSerializer.Deserialize<List<string>>(fileContent)!;
    }

    #endregion
}
