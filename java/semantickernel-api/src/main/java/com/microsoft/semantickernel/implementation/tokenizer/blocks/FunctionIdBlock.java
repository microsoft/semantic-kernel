// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.implementation.tokenizer.blocks;

import com.microsoft.semantickernel.orchestration.KernelFunctionArguments;

import javax.annotation.Nullable;

/**
 * Represents a function identifier block.
 */
public final class FunctionIdBlock extends Block implements TextRendering {
    private final String skillName;

    private final String functionName;

    /**
     * Initializes a new instance of the {@link FunctionIdBlock} class.
     *
     * @param content The content.
     */
    public FunctionIdBlock(String content) {
        super(content, BlockTypes.FunctionId);

        String[] functionNameParts = this.getContent().split("\\.", -1);
        if (functionNameParts.length > 2) {
            throw new RuntimeException(
                    "A function name can contain at most one dot separating the plugin name from the"
                            + " function name");
        }

        if (functionNameParts.length == 2) {
            this.skillName = functionNameParts[0];
            this.functionName = functionNameParts[1];
            return;
        }

        this.functionName = this.getContent();
        this.skillName = "";
    }

    @Override
    @Nullable
    public String render(@Nullable KernelFunctionArguments variables) {
        return this.getContent();
    }

    @Override
    public boolean isValid() {
        if (!this.getContent().matches("^[a-zA-Z0-9_.]*$")) {
            // errorMsg = "The function identifier is empty";
            return false;
        }

        if (hasMoreThanOneDot(this.getContent())) {
            // errorMsg = "The function identifier can contain max one '.' char separating skill
            // name from function name";
            return false;
        }

        // errorMsg = "";
        return true;
    }

    private static boolean hasMoreThanOneDot(String value) {
        if (value == null || value.length() < 2) {
            return false;
        }

        return value.matches("^.*\\..*\\..*$");
    }

    /**
     * Get the plugin name.
     *
     * @return The plugin name.
     */
    public String getPluginName() {
        return skillName;
    }

    /**
     * Get the function name.
     *
     * @return The function name.
     */
    public String getFunctionName() {
        return functionName;
    }
}
