// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import javax.annotation.Nullable;

public class Verify {
<<<<<<< HEAD

=======
>>>>>>> beeed7b7a795d8c989165740de6ddb21aeacbb6f
    public static void notNull(Object object) {
        assert object != null;
    }

    public static boolean isNullOrEmpty(@Nullable String s) {
        return s == null || s.isEmpty();
    }
<<<<<<< HEAD

    public static boolean isNullOrWhiteSpace(String s) {
        return s == null || s.matches("^\\w+$");
    }
=======
>>>>>>> beeed7b7a795d8c989165740de6ddb21aeacbb6f
}
