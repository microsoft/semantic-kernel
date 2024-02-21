// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.contextvariables.converters;

import static com.microsoft.semantickernel.contextvariables.ContextVariableTypes.convert;

import com.microsoft.semantickernel.contextvariables.ContextVariableTypeConverter;
import com.microsoft.semantickernel.contextvariables.ContextVariableTypes;

/**
 * A {@link ContextVariableTypeConverter} for {@code java.lang.Character} variables. Use
 * {@code ContextVariableTypes.getGlobalVariableTypeForClass(Character.class)} to get an instance of
 * this class.
 *
 * @see ContextVariableTypes#getGlobalVariableTypeForClass(Class)
 */
public class CharacterVariableContextVariableTypeConverter extends
    ContextVariableTypeConverter<Character> {

    /**
     * Initializes a new instance of the {@link CharacterVariableContextVariableTypeConverter}
     * class.
     */
    public CharacterVariableContextVariableTypeConverter() {
        super(
            Character.class,
            s -> convert(s, Character.class),
            Object::toString,
            CharacterVariableContextVariableTypeConverter::charFromPromptString);
    }

    /*
     * Converts a prompt string to a Character.
     */
    static Character charFromPromptString(String s) {
        if (s.length() != 1) {
            throw new IllegalArgumentException("Cannot convert string to character: " + s);
        }
        return s.charAt(0);
    }
}
