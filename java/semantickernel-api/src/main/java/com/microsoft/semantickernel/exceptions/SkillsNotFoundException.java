// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.exceptions;

import com.microsoft.semantickernel.SKException;

public class SkillsNotFoundException extends SKException {

    private final ErrorCodes errorCode;

    public SkillsNotFoundException(ErrorCodes errorCodes) {
        this(errorCodes, null, null);
    }

    public SkillsNotFoundException(ErrorCodes errorCodes, String message) {
        this(errorCodes, message, null);
    }

    public SkillsNotFoundException(ErrorCodes errorCodes, String message, Throwable cause) {
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
