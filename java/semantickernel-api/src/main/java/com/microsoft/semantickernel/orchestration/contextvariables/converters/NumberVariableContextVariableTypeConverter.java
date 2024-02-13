package com.microsoft.semantickernel.orchestration.contextvariables.converters;

import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypeConverter;
import static com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypes.convert;

import java.util.function.Function;

import javax.annotation.Nullable;

/**
 * A {@link ContextVariableTypeConverter} for {@link Number}.
 */
public class NumberVariableContextVariableTypeConverter<T extends Number> extends
    ContextVariableTypeConverter<T> {

    private final Function<Number, T> fromNumber;

    /**
     * Creates a new instance of the {@link NumberVariableContextVariableTypeConverter} class.
     * @param clazz the class
     * @param fromPromptString the function to convert from a prompt string
     * @param fromNumber the function to convert from a number
     */
    public NumberVariableContextVariableTypeConverter(
        Class<T> clazz,
        Function<String, T> fromPromptString,
        Function<Number, T> fromNumber
    ) {
        super(
            clazz,
            s -> convert(s, clazz),
            Number::toString,
            fromPromptString);
        this.fromNumber = fromNumber;
    }

    @Override
    @Nullable
    public <U> U toObject(@Nullable Object t, Class<U> clazz) {
        if (t == null) {
            return null;
        }

        // Let the parent class have a crack at it first
        // since someone may have installed a special converter. 
        U obj = super.toObject(t, clazz);
        if (obj != null) {
            return obj;
        }
        // If the type is a string, and the object is of the same type as the
        // converter, then we can convert with the toPromptString method.
        if (clazz == String.class && t.getClass() == super.getType()) {
            return clazz.cast(toPromptString(getType().cast(t)));
        }
        return null;
    }

    @Override
    @Nullable
    public T fromObject(@Nullable Object s) {
        T obj = super.fromObject(s);
        if (obj != null) {
            return obj;
        }

        if (s instanceof Number) {
            return fromNumber.apply((Number) s);
        }

        if (s instanceof String) {
            return fromPromptString((String) s);
        }
        return null;
    }

    @Override
    @Nullable
    public T fromPromptString(@Nullable String s) {
        if (s != null && !s.isEmpty()) {
            return super.fromPromptString(s);
        }
        return null;
    }

}
