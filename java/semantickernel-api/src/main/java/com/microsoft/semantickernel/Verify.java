// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

public class Verify {
    public static void notNull(Object object) {
        assert object != null;
    }

    public static boolean isNullOrEmpty(String s) {
        return s == null || s.isEmpty();
    }
}
