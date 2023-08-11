// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.exceptions;

import com.microsoft.semantickernel.SKException;

public class NotSupportedException extends SKException {

  private final ErrorCodes errorCode;

  public NotSupportedException(ErrorCodes errorCode) {
    this(errorCode, null, null);
  }

  public NotSupportedException(ErrorCodes errorCode, String message) {
    this(errorCode, message, null);
  }

  public NotSupportedException(ErrorCodes errorCode, String message, Throwable cause) {
    super(formatDefaultMessage(errorCode.getMessage(), message), cause);
    this.errorCode = errorCode;
  }

  public ErrorCodes getErrorCode() {
    return errorCode;
  }

  public enum ErrorCodes {
    NOT_SUPPORTED("Not Supported");

    final String message;

    ErrorCodes(String message) {
      this.message = message;
    }

    String getMessage() { return message; }
  }
}
