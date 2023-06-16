// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.coreskills;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

public class MathSkillTest {

    @Test
    public void testAddition() {
        MathSkill mathSkill = new MathSkill();
        String result = mathSkill.add("1", "2");
        assertEquals("3", result);
    }

    @Test
    public void testSubtraction() {
        MathSkill mathSkill = new MathSkill();
        String result = mathSkill.subtract("1", "2");
        assertEquals("-1", result);
    }
}
