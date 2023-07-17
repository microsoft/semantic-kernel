// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.Tokenizers;

// ReSharper disable once InconsistentNaming
/// <summary>
/// This sample shows how to count tokens using GPT tokenizer. The number of tokens affects
/// API calls cost and each models has a maximum amount of tokens it can process and generate.
/// This example is specific to OpenAI models, which use the tokenization described here:
/// https://platform.openai.com/tokenizer
/// If you use Semantic Kernel with other models, the tokenization logic is most probably different,
/// and you should not use the GPT tokenizer.
/// </summary>
public static class Example29_Tokenizer
{
    public static Task RunAsync()
    {
        // Example 1
        string sentence = "Some text on one line";
        int tokenCount = GPT3Tokenizer.Encode(sentence).Count;

        Console.WriteLine("---");
        Console.WriteLine(sentence);
        Console.WriteLine("Tokens: " + tokenCount);
        Console.WriteLine("---\n\n");

        // Example 2
        sentence = "⭐⭐";
        tokenCount = GPT3Tokenizer.Encode(sentence).Count;

        Console.WriteLine("The following example contains emojis which require several tokens.");
        Console.WriteLine("---");
        Console.WriteLine(sentence);
        Console.WriteLine("Tokens: " + tokenCount);
        Console.WriteLine("---\n\n");

        // Example 3
        sentence = "Some text on\ntwo lines";
        tokenCount = GPT3Tokenizer.Encode(sentence).Count;

        Console.WriteLine("The following example uses Unix '\\n' line separator.");
        Console.WriteLine("---");
        Console.WriteLine(sentence);
        Console.WriteLine("Tokens: " + tokenCount);
        Console.WriteLine("---\n\n");

        // Example 4
        sentence = "Some text on\r\ntwo lines";
        tokenCount = GPT3Tokenizer.Encode(sentence).Count;

        Console.WriteLine("The following example uses Windows '\\r\\n' line separator.");
        Console.WriteLine("---");
        Console.WriteLine(sentence);
        Console.WriteLine("Tokens: " + tokenCount);
        Console.WriteLine("---\n\n");

        /*
        Output:
        ---
        Some text on one line
        Tokens: 5
        ---


        The following example contains emojis which require several tokens.
        ---
        ⭐⭐
        Tokens: 6
        ---


        The following example uses Unix '\n' line separator.
        ---
        Some text on
        two lines
        Tokens: 6
        ---


        The following example uses Windows '\r\n' line separator.
        ---
        Some text on
        two lines
        Tokens: 7
        ---
         */

        return Task.CompletedTask;
    }
}
