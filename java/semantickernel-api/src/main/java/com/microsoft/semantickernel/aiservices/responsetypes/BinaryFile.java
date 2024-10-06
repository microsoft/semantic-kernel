package com.microsoft.semantickernel.aiservices.responsetypes;

import java.util.UUID;

public interface BinaryFile {
    UUID getId();
    String contentType();
    byte[] getBytes();
}
