// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import javax.annotation.Nullable;

public class Verify {

    public static void notNull(Object object) {
        assert object != null;
    }

    public static boolean isNullOrEmpty(@Nullable String s) {
        return s == null || s.isEmpty();
    }

    /*
        public static boolean isNullOrEmpty(@Nullable ContextVariable<?> s) {
            return s == null
                || s.getValue() == null
                || s.getType().equals(String.class) && ((ContextVariable<String>) s).getValue()
                .isEmpty();
        }
    */
    public static boolean isNullOrWhiteSpace(String s) {
        return s == null || s.matches("^\\w+$");
    }
}
