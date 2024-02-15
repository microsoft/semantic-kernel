// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.implementation.templateengine.tokenizer.blocks;

import com.microsoft.semantickernel.semanticfunctions.KernelFunctionArguments;
import com.microsoft.semantickernel.contextvariables.ContextVariable;
import com.microsoft.semantickernel.templateengine.semantickernel.TemplateException;
import javax.annotation.Nullable;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public final class VarBlock extends Block implements TextRendering {

    private static final Logger LOGGER = LoggerFactory.getLogger(VarBlock.class);
    private final String name;

    public VarBlock(String content) {
        super(content, BlockTypes.Variable);

        if (content.length() < 2) {
            LOGGER.error("The variable name is empty");
        }

        this.name = content.substring(1);
    }

    @Override
    public String render(@Nullable KernelFunctionArguments variables) {
        if (variables == null) {
            return "";
        }

        if (name == null || name.isEmpty()) {
            throw new TemplateException(
                TemplateException.ErrorCodes.SYNTAX_ERROR,
                "Variable rendering failed, the variable name is empty");
        }

        ContextVariable<?> value = variables.get(
            name);

        if (value == null) {
            LOGGER.warn("Variable `{}{}` not found", Symbols.VarPrefix, name);
        }

        return value != null ? value.toPromptString() : "";
    }

    @Override
    public boolean isValid() {
        if (getContent() == null || getContent().isEmpty()) {
            LOGGER.error(
                "A variable must start with the symbol {} and have a name", Symbols.VarPrefix);
            return false;
        }

        if (getContent().charAt(0) != Symbols.VarPrefix) {
            LOGGER.error("A variable must start with the symbol {}", Symbols.VarPrefix);
            return false;
        }

        if (getContent().length() < 2) {
            LOGGER.error("The variable name is empty");
            return false;
        }

        if (!name.matches("^[a-zA-Z0-9_]*$")) {
            LOGGER.error(
                "The variable name '{}' contains invalid characters. "
                    + "Only alphanumeric chars and underscore are allowed.",
                name);
            return false;
        }

        return true;
    }

    public String getName() {
        return name;
    }
}
