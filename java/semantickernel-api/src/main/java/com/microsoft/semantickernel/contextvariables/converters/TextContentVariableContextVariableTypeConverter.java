// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.contextvariables.converters;

import static com.microsoft.semantickernel.contextvariables.ContextVariableTypes.convert;

import com.microsoft.semantickernel.contextvariables.ContextVariableTypeConverter;
import com.microsoft.semantickernel.services.textcompletion.TextContent;
import javax.annotation.Nullable;

/**
 * A converter for a context variable type. This class is used to convert objects to and from a
 * prompt string, and to convert objects to the type of the context variable.
 */
public class TextContentVariableContextVariableTypeConverter extends
    ContextVariableTypeConverter<TextContent> {

    /**
     * Initializes a new instance of the {@link TextContentVariableContextVariableTypeConverter}
     * class.
     */
    public TextContentVariableContextVariableTypeConverter() {
        super(
            TextContent.class,
            s -> convert(s, TextContent.class),
            TextContentVariableContextVariableTypeConverter::escapeXmlStringValue,
            x -> {
                throw new UnsupportedOperationException(
                    "TextContentVariableContextVariableTypeConverter does not support fromPromptString");
            });
    }

    @Nullable
    public static String escapeXmlStringValue(@Nullable TextContent value) {
        if (value == null) {
            return null;
        }
        return escapeXmlString(value.getContent());
    }
}
