// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import javax.annotation.Nullable;

/**
 * Provides methods for verifying the state of objects and strings in 
 * a consistent manner.
 */
public class Verify {

    /**
     * Verifies that the given object is not null.
     * @param object The object to verify.
     */
    public static void notNull(Object object) {
        assert object != null;
    }

    /**
     * Verifies that the given object is null or empty.
     * @param s The String to verify.
     * @return true if the object is null or empty; otherwise, false.
     */
    public static boolean isNullOrEmpty(@Nullable String s) {
        return s == null || s.isEmpty();
    }

    /**
     * Verifies that the given object is null or contains only whitespace.
     * @param s The String to verify.
     * @return true if the object is null or whitespace; otherwise, false.
     */
    public static boolean isNullOrWhiteSpace(String s) {
        return s == null || s.matches("^\\w+$");
    }
}
