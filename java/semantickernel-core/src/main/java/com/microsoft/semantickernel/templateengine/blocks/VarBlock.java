// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.templateengine.blocks;

import com.microsoft.semantickernel.orchestration.ContextVariables;
import com.microsoft.semantickernel.templateengine.TemplateException;
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
    public String render(ContextVariables variables) {
        if (variables == null) {
            return "";
        }

        if (name == null || name.isEmpty()) {
            throw new TemplateException(
                    TemplateException.ErrorCodes.SyntaxError,
                    "Variable rendering failed, the variable name is empty");
        }

        String value = variables.asMap().get(name);

        if (value == null) {

            LOGGER.warn("Variable `{}{}` not found", Symbols.VarPrefix, name);
        }

        return value != null ? value : "";
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
