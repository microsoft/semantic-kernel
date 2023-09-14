// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Text;
using SharpToken;

// ReSharper disable once InconsistentNaming
public static class Example55_TextChunker
{
    private const string text = @"The city of Venice, located in the northeastern part of Italy,
is renowned for its unique geographical features. Built on more than 100 small islands in a lagoon in the
Adriatic Sea, it has no roads, just canals including the Grand Canal thoroughfare lined with Renaissance and
Gothic palaces. The central square, Piazza San Marco, contains St. Mark's Basilica, which is tiled with Byzantine
mosaics, and the Campanile bell tower offering views of the city's red roofs.

The Amazon Rainforest, also known as Amazonia, is a moist broadleaf tropical rainforest in the Amazon biome that
covers most of the Amazon basin of South America. This basin encompasses 7 million square kilometers, of which
5.5 million square kilometers are covered by the rainforest. This region includes territory belonging to nine nations
and 3.4 million square kilometers of uncontacted tribes. The Amazon represents over half of the planet's remaining
rainforests and comprises the largest and most biodiverse tract of tropical rainforest in the world.

The Great Barrier Reef is the world's largest coral reef system composed of over 2,900 individual reefs and 900 islands
stretching for over 2,300 kilometers over an area of approximately 344,400 square kilometers. The reef is located in the
Coral Sea, off the coast of Queensland, Australia. The Great Barrier Reef can be seen from outer space and is the world's
biggest single structure made by living organisms. This reef structure is composed of and built by billions of tiny organisms,
known as coral polyps.";

    public static Task RunAsync()
    {
        RunExample();
        RunExampleWithCustomTokenCounter();

        return Task.CompletedTask;
    }

    private static void RunExample()
    {
        Console.WriteLine("=== Text chunking ===");

        var lines = TextChunker.SplitPlainTextLines(text, 40);
        var paragraphs = TextChunker.SplitPlainTextParagraphs(lines, 120);

        WriteParagraphsToConsole(paragraphs);
    }

    private static void RunExampleWithCustomTokenCounter()
    {
        Console.WriteLine("=== Text chunking with a custom token counter ===");

        var lines = TextChunker.SplitPlainTextLines(text, 40, CustomTokenCounter);
        var paragraphs = TextChunker.SplitPlainTextParagraphs(lines, 120, tokenCounter: CustomTokenCounter);

        WriteParagraphsToConsole(paragraphs);
    }

    private static void WriteParagraphsToConsole(List<string> paragraphs)
    {
        for (var i = 0; i < paragraphs.Count; i++)
        {
            Console.WriteLine(paragraphs[i]);

            if (i < paragraphs.Count - 1)
            {
                Console.WriteLine("------------------------");
            }
        }
    }

    /// <summary>
    /// Custom token counter implementation using SharpToken.
    /// Note: SharpToken is used for demonstration purposes only, it's possible to use any available or custom tokenization logic.
    /// </summary>
    private static int CustomTokenCounter(string input)
    {
        // Initialize encoding by encoding name
        var encoding = GptEncoding.GetEncoding("cl100k_base");

        // Initialize encoding by model name
        // var encoding = GptEncoding.GetEncodingForModel("gpt-4");

        var tokens = encoding.Encode(input);

        return tokens.Count;
    }
}
