// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import javax.annotation.Nullable;

/**
 * Provides methods for verifying the state of objects and strings in 
 * a consistent manner.
 */
public class Verify {

    public static void notNull(Object object) {
        assert object != null;
    }

    public static boolean isNullOrEmpty(@Nullable String s) {
        return s == null || s.isEmpty();
    }

    public static boolean isNullOrWhiteSpace(String s) {
        return s == null || s.matches("^\\w+$");
    }
}
