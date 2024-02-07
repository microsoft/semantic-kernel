package com.microsoft.semantickernel.orchestration.contextvariables.converters;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableType;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypeConverter;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypes;
 
public class NumberVariableContextVariableTypeConverterTest {

    /**
     * Test of toObject method, of class NumberVariableContextVariableTypeConverter.
     */
    @Test
    void testConvertIntegerToString() {
        ContextVariableType<Integer> type = ContextVariableTypes.getGlobalVariableTypeForClass(Integer.class);
        ContextVariableTypeConverter<Integer> instance = type.getConverter();
        Object expResult = "1";
        Object result = instance.toObject(1, String.class);
        assertEquals(expResult, result);
    }

    /**
     * Test of fromObject method, of class NumberVariableContextVariableTypeConverter.
     */
    @Test
    void  testFromStringToInteger() {
        Object s = "123";
        ContextVariableType<Integer> type = ContextVariableTypes.getGlobalVariableTypeForClass(Integer.class);
        ContextVariableTypeConverter<Integer> instance = type.getConverter();
        Number expResult = Integer.valueOf((String)s);
        Number result = instance.fromObject(s);
        assertEquals(expResult, result);
    }

    @Test
    void testFromPromptStringToInteger() {
        String s = "123";
        ContextVariableType<Integer> type = ContextVariableTypes.getGlobalVariableTypeForClass(Integer.class);
        ContextVariableTypeConverter<Integer> instance = type.getConverter();
        Number expResult = Integer.valueOf(s);
        Number result = instance.fromPromptString(s);
        assertEquals(expResult, result);
    }

    @Test
    void testFromPromptStringReturnsNullForEmptyString() {
        String s = "";
        ContextVariableType<Integer> type = ContextVariableTypes.getGlobalVariableTypeForClass(Integer.class);
        ContextVariableTypeConverter<Integer> instance = type.getConverter();
        Number expResult = null;
        Number result = instance.fromPromptString(s);
        assertEquals(expResult, result);
    }

    @Test
    void testFromPromptStringReturnsNullForNullString() {
        String s = null;
        ContextVariableType<Integer> type = ContextVariableTypes.getGlobalVariableTypeForClass(Integer.class);
        ContextVariableTypeConverter<Integer> instance = type.getConverter();
        Number expResult = null;
        Number result = instance.fromPromptString(s);
        assertEquals(expResult, result);
    }

    @Test
    void testToPromptString() {
        Integer num = 123;
        ContextVariableType<Integer> type = ContextVariableTypes.getGlobalVariableTypeForClass(Integer.class);
        ContextVariableTypeConverter<Integer> instance = type.getConverter();
        String expResult = "123";
        String result = instance.toPromptString(num);
        assertEquals(expResult, result);
    }

    @Test
    void testToPromptStringReturnsEmptyStringForNull() {
        Integer num = null;
        ContextVariableType<Integer> type = ContextVariableTypes.getGlobalVariableTypeForClass(Integer.class);
        ContextVariableTypeConverter<Integer> instance = type.getConverter();
        String expResult = "";
        String result = instance.toPromptString(num);
        assertEquals(expResult, result);
    }

}