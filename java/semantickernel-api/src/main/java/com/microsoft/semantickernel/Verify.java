// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.microsoft.semantickernel.orchestration.ContextVariable;
import com.microsoft.semantickernel.orchestration.contextvariables.PrimativeContextVariable.StringVariable;
import javax.annotation.Nullable;

public class Verify {

    public static void notNull(Object object) {
        assert object != null;
    }

    public static boolean isNullOrEmpty(@Nullable String s) {
        return s == null || s.isEmpty();
    }

    public static boolean isNullOrEmpty(@Nullable ContextVariable<?> s) {
        return s == null
                || s instanceof StringVariable && ((StringVariable) s).getValue().isEmpty();
    }

    public static boolean isNullOrWhiteSpace(String s) {
        return s == null || s.matches("^\\w+$");
    }
}
