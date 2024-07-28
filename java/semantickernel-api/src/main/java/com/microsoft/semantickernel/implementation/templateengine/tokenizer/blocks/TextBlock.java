// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.implementation.templateengine.tokenizer.blocks;

import com.microsoft.semantickernel.contextvariables.ContextVariableTypes;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionArguments;
import javax.annotation.Nullable;

public final class TextBlock extends Block implements TextRendering {

    public TextBlock(String text) {
        super(text, BlockTypes.TEXT);
    }

    public TextBlock(String text, int startIndex, int stopIndex) {
        super(text.substring(startIndex, stopIndex), BlockTypes.TEXT);
    }

    @Override
    public boolean isValid() {
        return true;
    }

    @Override
    public String render(ContextVariableTypes types, @Nullable KernelFunctionArguments variables) {
        return super.getContent();
    }
}
