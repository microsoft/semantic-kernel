// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.coreskills;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

import java.math.BigDecimal;

public class MathSkillTest {

    @Test
    public void testAddition() {
        MathSkill mathSkill = new MathSkill();
        BigDecimal result = mathSkill.add("1", new BigDecimal("2")).block();
        assertEquals(new BigDecimal("3"), result);
    }

    @Test
    public void testSubtraction() {
        MathSkill mathSkill = new MathSkill();
        BigDecimal result = mathSkill.subtract("1", new BigDecimal("2")).block();
        assertEquals(new BigDecimal("-1"), result);
    }
}
