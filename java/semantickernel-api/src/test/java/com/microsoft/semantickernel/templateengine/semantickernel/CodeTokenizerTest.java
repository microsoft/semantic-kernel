// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.templateengine.semantickernel;

import java.util.List;

import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;

import com.microsoft.semantickernel.orchestration.KernelFunctionArguments;
import com.microsoft.semantickernel.templateengine.semantickernel.blocks.Block;
import com.microsoft.semantickernel.templateengine.semantickernel.blocks.FunctionIdBlock;
import com.microsoft.semantickernel.templateengine.semantickernel.blocks.NamedArgBlock;

public class CodeTokenizerTest {

    @Test
    public void parseNamedArgs1() {
        List<Block> tokens = new CodeTokenizer().tokenize(
            "MyFunction street=$street zip=\"98123\" city=\"Seattle\"");

        Assertions.assertEquals(4, tokens.size());

        FunctionIdBlock function = (FunctionIdBlock) tokens.get(0);
        Assertions.assertEquals("MyFunction", function.getFunctionName());
        Assertions.assertEquals("", function.getPluginName());

        NamedArgBlock namedArgBlock = (NamedArgBlock) tokens.get(1);
        Assertions.assertEquals("street", namedArgBlock.getName());
        Assertions.assertEquals("123 Main St", namedArgBlock.getValue(
            new KernelFunctionArguments.Builder()
                .withVariable("street", "123 Main St")
                .build()));

        namedArgBlock = (NamedArgBlock) tokens.get(2);
        Assertions.assertEquals("zip", namedArgBlock.getName());
        Assertions.assertEquals("98123", namedArgBlock.getValue(
            new KernelFunctionArguments.Builder().build()));

        namedArgBlock = (NamedArgBlock) tokens.get(3);
        Assertions.assertEquals("city", namedArgBlock.getName());
        Assertions.assertEquals("Seattle", namedArgBlock.getValue(
            new KernelFunctionArguments.Builder().build()));
    }

    @Test
    public void parseNamedArgs2() {
        List<Block> tokens = new CodeTokenizer().tokenize(
            "MyFunction recall='where did I grow up?'");

        Assertions.assertEquals(2, tokens.size());

        FunctionIdBlock function = (FunctionIdBlock) tokens.get(0);
        Assertions.assertEquals("MyFunction", function.getFunctionName());
        Assertions.assertEquals("", function.getPluginName());

        NamedArgBlock namedArgBlock = (NamedArgBlock) tokens.get(1);
        Assertions.assertEquals("recall", namedArgBlock.getName());
        Assertions.assertEquals("where did I grow up?", namedArgBlock.getValue(
            new KernelFunctionArguments.Builder()
                .build()));
    }
}
