// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.exceptions;

import com.microsoft.semantickernel.SKException;

public class NotSupportedException extends SKException {
    public NotSupportedException(String s) {
        super(s);
    }
}
