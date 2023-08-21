// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.planner;

import com.microsoft.semantickernel.SKException;
import javax.annotation.Nonnull;
import javax.annotation.Nullable;

/** Exception thrown for errors related to planning. */
public class PlanningException extends SKException {
    @Nonnull private final ErrorCodes errorCode;

    public PlanningException(@Nonnull ErrorCodes error) {
        this(error, null, null);
    }

    /**
     * Initializes a new instance of the PlanningException class with a provided error code and
     * message
     *
     * @param errorCode Error code
     * @param message The exception message
     */
    public PlanningException(@Nonnull ErrorCodes errorCode, @Nullable String message) {
        this(errorCode, message, null);
    }

    /**
     * Initializes a new instance of the PlanningException class with a provided error code,
     * message, and inner exception.
     *
     * @param errorCode The error code
     * @param message A string that describes the error
     * @param innerException The exception that is the cause of the current exception
     */
    public PlanningException(
            @Nonnull ErrorCodes errorCode,
            @Nullable String message,
            @Nullable Throwable innerException) {
        super(formatDefaultMessage(errorCode.getMessage(), message), innerException);
        this.errorCode = errorCode;
    }

    /**
     * Gets the error code
     *
     * @return The error code
     */
    public ErrorCodes getErrorCode() {
        return errorCode;
    }

    /** Error codes for PlanningException */
    public enum ErrorCodes {
        UNKNOWN_ERROR("Unknown error"),

        INVALID_GOAL("Invalid goal"),

        INVALID_PLAN("Invalid plan"),

        INVALID_CONFIGURATION("Invalid configuration"),
        PLAN_EXECUTION_PRODUCED_NO_RESULTS("Plan execution produced no result values");

        private final String message;

        ErrorCodes(String message) {
            this.message = message;
        }

        public String getMessage() {
            return message;
        }
    }
}
