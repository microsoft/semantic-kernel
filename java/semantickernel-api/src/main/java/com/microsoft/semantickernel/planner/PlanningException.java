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
        super(getDefaultMessage(errorCode, message), innerException);
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

    /* Translate the error code into a default message */
    private static String getDefaultMessage(
            @Nonnull ErrorCodes errorCode, @Nullable String message) {
        return String.format("%s: %s", errorCode.getMessage(), message);
    }

    /** Error codes for PlanningException */
    public enum ErrorCodes {
        UnknownError("Unknown error"),

        InvalidGoal("Invalid goal"),

        InvalidPlan("Invalid plan"),

        InvalidConfiguration("Invalid configuration"),
        PlanExecutionProducedNoResults("Plan execution produced no result values");

        private final String message;

        ErrorCodes(String message) {
            this.message = message;
        }

        public String getMessage() {
            return message;
        }
    }
}
