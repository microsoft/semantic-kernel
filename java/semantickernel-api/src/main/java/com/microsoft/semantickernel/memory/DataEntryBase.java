// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.memory;

import java.time.ZonedDateTime;
import javax.annotation.Nonnull;
import javax.annotation.Nullable;

/** A base class for data entries. */
public class DataEntryBase {
    @Nonnull private final String key;
    @Nullable private final ZonedDateTime timestamp;

    /**
     * Creates an instance of a {@code DataEntryBase}.
     *
     * @param key The key of the data.
     * @param timestamp The timestamp of the data.
     */
    public DataEntryBase(@Nullable String key, @Nullable ZonedDateTime timestamp) {
        this.key = key != null ? key : "";
        this.timestamp = timestamp;
    }

    /**
     * Gets the key of the data.
     *
     * @return The key of the data
     */
    public String getKey() {
        return key;
    }

    /**
     * Gets the timestamp of the data.
     *
     * @return The timestamp of the data.
     */
    @Nullable
    public ZonedDateTime getTimestamp() {
        return timestamp;
    }
}
