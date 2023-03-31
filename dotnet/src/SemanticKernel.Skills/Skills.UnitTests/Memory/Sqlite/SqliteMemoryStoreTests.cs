// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Skills.Memory.Sqlite;
using Xunit;

namespace SemanticKernel.Skills.UnitTests.Memory.Sqlite;

/// <summary>
/// Unit tests of <see cref="SqliteMemoryStoreMemoryStore"/>.
/// </summary>
public class SqliteDataStoreTests : IDisposable
{
    private const string DatabaseFile = "SqliteDataStoreTests.db";
    private SqliteMemoryStore? _db = null;
    private bool _disposedValue;

    public SqliteDataStoreTests()
    {
        File.Delete(DatabaseFile);
    }

    protected virtual void Dispose(bool disposing)
    {
        if (!this._disposedValue)
        {
            if (disposing)
            {
                this._db?.Dispose();
                File.Delete(DatabaseFile);
            }

            this._disposedValue = true;
        }
    }

    public void Dispose()
    {
        // Do not change this code. Put cleanup code in 'Dispose(bool disposing)' method
        this.Dispose(disposing: true);
        GC.SuppressFinalize(this);
    }
}
