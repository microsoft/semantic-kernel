package com.microsoft.semantickernel.orchestration.contextvariables.converters;

import java.util.function.Function;

import javax.annotation.Nullable;

import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypeConverter;
import static com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypes.convert;

public class NumberVariableContextVariableTypeConverter<T extends Number> extends
    ContextVariableTypeConverter<T> {

    public NumberVariableContextVariableTypeConverter(Class<T> clazz,
        Function<String, T> fromPromptString) {
        super(
            clazz,
            s -> convert(s, clazz),
            Number::toString,
            fromPromptString);
    }

    @Override
    @Nullable
    public <U> U toObject(Object t, Class<U> clazz) {
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
    public T fromObject(Object s) {
        T obj = super.fromObject(s);
        if (obj != null) {
            return obj; 
        }
        if (s instanceof String) {
            return fromPromptString((String) s);
        }
        return null;
    }

    @Override
    public T fromPromptString(String s) {
        if (s != null && !s.isEmpty()) {
            return super.fromPromptString(s);
        }
        return null; 
    }

}
