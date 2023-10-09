// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.memory.jdbc;

import static org.junit.jupiter.api.Assertions.*;

import java.util.ArrayList;
import java.util.Collection;
import org.junit.jupiter.api.Test;

public class JDBCConnectorTest {
    @Test
    void testBatchQuery() {
        Collection<String> keys = new ArrayList<>();
        keys.add("key1");
        keys.add("key2");
        keys.add("key3");

        JDBCConnector connector = new JDBCConnector(null);
        String read = connector.batchQuery(JDBCConnector.BatchOperation.SELECT, keys);
        String delete = connector.batchQuery(JDBCConnector.BatchOperation.DELETE, keys);

        assertNotNull(read);
        assertNotNull(delete);
        assertEquals(
                "SELECT * FROM "
                        + JDBCConnector.TABLE_NAME
                        + " WHERE collectionId = ? AND id IN (?,?,?)",
                read);
        assertEquals(
                "DELETE FROM "
                        + JDBCConnector.TABLE_NAME
                        + " WHERE collectionId = ? AND id IN (?,?,?)",
                delete);
    }
}
