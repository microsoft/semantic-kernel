package com.microsoft.semantickernel.samples.syntaxexamples;

import com.microsoft.semantickernel.GPT3Tokenizer;
public class Example29_Tokenizer {
    /**
     * This sample shows how to count tokens using GPT tokenizer. The number of tokens affects
     * API calls cost and each model has a maximum amount of tokens it can process and generate.
     * This example is specific to OpenAI models, which use the tokenization described here:
     * <a href="https://platform.openai.com/tokenizer">OpenAI tokenizer</a>
     * If you use Semantic Kernel with other models, the tokenization logic is most probably different,
     * and you should not use the GPT tokenizer.
     */
    public static void main(String[] args) {
        // Example 1
        String sentence = "Some text on one line";
        int tokenCount = GPT3Tokenizer.encode(sentence).size();

        System.out.println("---");
        System.out.println(sentence);
        System.out.println("Tokens: " + tokenCount);
        System.out.println("---\n\n");

        // Example 2
        sentence = "⭐⭐";
        tokenCount = GPT3Tokenizer.encode(sentence).size();

        System.out.println("The following example contains emojis which require several tokens.");
        System.out.println("---");
        System.out.println(sentence);
        System.out.println("Tokens: " + tokenCount);
        System.out.println("---\n\n");

        // Example 3
        sentence = "Some text on\ntwo lines";
        tokenCount = GPT3Tokenizer.encode(sentence).size();

        System.out.println("The following example uses Unix '\\n' line separator.");
        System.out.println("---");
        System.out.println(sentence);
        System.out.println("Tokens: " + tokenCount);
        System.out.println("---\n\n");

        // Example 4
        sentence = "Some text on\r\ntwo lines";
        tokenCount = GPT3Tokenizer.encode(sentence).size();

        System.out.println("The following example uses Windows '\\r\\n' line separator.");
        System.out.println("---");
        System.out.println(sentence);
        System.out.println("Tokens: " + tokenCount);
        System.out.println("---\n\n");

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
    }
}
