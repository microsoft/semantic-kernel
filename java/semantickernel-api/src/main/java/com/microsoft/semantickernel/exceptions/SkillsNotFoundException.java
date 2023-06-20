// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.exceptions;

import com.microsoft.semantickernel.SKException;

public class SkillsNotFoundException extends SKException {
    public SkillsNotFoundException(String msg) {
        super(msg);
    }

    public SkillsNotFoundException() {}
}
