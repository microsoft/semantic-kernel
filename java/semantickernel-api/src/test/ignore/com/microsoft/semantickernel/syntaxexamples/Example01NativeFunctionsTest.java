// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.syntaxexamples;

import com.microsoft.semantickernel.coreskills.TextSkill;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;

public class Example01NativeFunctionsTest {

    @Test
    public void run() {
        // Load native skill
        TextSkill text = new TextSkill();

        // Use function without kernel
        String result = text.uppercase("ciao!");

        Assertions.assertEquals("CIAO!", result);
    }
}
