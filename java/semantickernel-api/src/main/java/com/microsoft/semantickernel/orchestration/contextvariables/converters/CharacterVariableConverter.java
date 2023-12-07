package com.microsoft.semantickernel.orchestration.contextvariables.converters;

import com.microsoft.semantickernel.orchestration.contextvariables.Converter;

import static com.microsoft.semantickernel.orchestration.contextvariables.VariableTypes.convert;

public class CharacterVariableConverter extends Converter<Character> {

    public CharacterVariableConverter() {
        super(
            Character.class,
            s -> convert(s, Character.class),
            Object::toString,
            CharacterVariableConverter::charToPromptString);
    }

    static Character charToPromptString(String s) {
        if (s.length() != 1) {
            throw new IllegalArgumentException("Cannot convert string to character: " + s);
        }
        return s.charAt(0);
    }
}
