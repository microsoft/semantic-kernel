// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.exceptions;

import com.microsoft.semantickernel.SKException;
import javax.annotation.Nonnull;
import javax.annotation.Nullable;

public class SkillsNotFoundException extends SKException {

    private final ErrorCodes errorCode;

    public SkillsNotFoundException(@Nonnull ErrorCodes errorCodes) {
        this(errorCodes, null, null);
    }

    public SkillsNotFoundException(@Nonnull ErrorCodes errorCodes, @Nullable String message) {
        this(errorCodes, message, null);
    }

    public SkillsNotFoundException(
            @Nonnull ErrorCodes errorCodes, @Nullable String message, @Nullable Throwable cause) {
        super(formatDefaultMessage(errorCodes.getMessage(), message), cause);
        this.errorCode = errorCodes;
    }

    public ErrorCodes getErrorCode() {
        return errorCode;
    }

    public enum ErrorCodes {
        SKILLS_NOT_FOUND("Skills not found");

        final String message;

        ErrorCodes(String message) {
            this.message = message;
        }

        String getMessage() {
            return message;
        }
    }
}
