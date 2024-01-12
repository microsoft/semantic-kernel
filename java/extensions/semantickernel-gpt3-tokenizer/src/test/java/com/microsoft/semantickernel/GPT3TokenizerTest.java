// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;

public class GPT3TokenizerTest {

    @Test
    public void tokenizerTest() {
        String sentence = "Some text on one line";
        int tokenCount = GPT3Tokenizer.encode(sentence).size();
        Assertions.assertEquals(5, tokenCount);

        sentence = "Some text on\r\ntwo lines";
        tokenCount = GPT3Tokenizer.encode(sentence).size();
        Assertions.assertEquals(7, tokenCount);

        // Sample from: https://platform.openai.com/tokenizer
        sentence =
                "Many words map to one token, but some don't: indivisible.\n"
                    + "\n"
                    + "Unicode characters like emojis may be split into many tokens containing the"
                    + " underlying bytes: \uD83E\uDD1A\uD83C\uDFFE\n"
                    + "\n"
                    + "Sequences of characters commonly found next to each other may be grouped"
                    + " together: 1234567890";
        tokenCount = GPT3Tokenizer.encode(sentence).size();
        Assertions.assertEquals(64, tokenCount);
    }
}
