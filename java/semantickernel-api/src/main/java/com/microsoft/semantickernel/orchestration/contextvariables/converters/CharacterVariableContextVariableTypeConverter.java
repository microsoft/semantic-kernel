package com.microsoft.semantickernel.orchestration.contextvariables.converters;

import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypeConverter;

import static com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypes.convert;

public class CharacterVariableContextVariableTypeConverter extends
    ContextVariableTypeConverter<Character> {

    public CharacterVariableContextVariableTypeConverter() {
        super(
            Character.class,
            s -> convert(s, Character.class),
            Object::toString,
            CharacterVariableContextVariableTypeConverter::charToPromptString);
    }

    static Character charToPromptString(String s) {
        if (s.length() != 1) {
            throw new IllegalArgumentException("Cannot convert string to character: " + s);
        }
        return s.charAt(0);
    }
}
