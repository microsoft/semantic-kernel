package com.microsoft.semantickernel.orchestration.contextvariables.converters;

import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypeConverter;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypes;
import static com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypes.convert;

/**
 * A {@link ContextVariableTypeConverter} for {@link Character} variables. Use
 * {@code ContextVariableTypes.getDefaultVariableTypeForClass(Character.class)} 
 * to get an instance of this class.
 * @see ContextVariableTypes#getDefaultVariableTypeForClass
 */
public class CharacterVariableContextVariableTypeConverter extends
    ContextVariableTypeConverter<Character> {

    /**
     * Initializes a new instance of the {@link CharacterVariableContextVariableTypeConverter} class.
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
