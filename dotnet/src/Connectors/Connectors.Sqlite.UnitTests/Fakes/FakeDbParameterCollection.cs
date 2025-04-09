// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Data.Common;

namespace SemanticKernel.Connectors.Sqlite.UnitTests;

#pragma warning disable CA1812

internal sealed class FakeDbParameterCollection : DbParameterCollection
{
    private readonly List<object> _parameters = [];

    public override int Count => this._parameters.Count;

    public override object SyncRoot => throw new NotImplementedException();

    public override int Add(object value)
    {
        this._parameters.Add(value);
        return default;
    }

    public override void AddRange(Array values)
    {
        this._parameters.AddRange([.. values]);
    }

    public override void Clear()
    {
        this._parameters.Clear();
    }

    public override bool Contains(object value)
    {
        return this._parameters.Contains(value);
    }

    public override bool Contains(string value)
    {
        return this._parameters.Contains(value);
    }

    public override void CopyTo(Array array, int index)
    {
        this._parameters.CopyTo([.. array], index);
    }

    public override IEnumerator GetEnumerator()
    {
        return this._parameters.GetEnumerator();
    }

    public override int IndexOf(object value)
    {
        return this._parameters.IndexOf(value);
    }

    public override int IndexOf(string parameterName)
    {
        return this._parameters.IndexOf(parameterName);
    }

    public override void Insert(int index, object value)
    {
        this._parameters.Insert(index, value);
    }

    public override void Remove(object value)
    {
        this._parameters.Remove(value);
    }

    public override void RemoveAt(int index)
    {
        this._parameters.RemoveAt(index);
    }

    public override void RemoveAt(string parameterName)
    {
        throw new NotImplementedException();
    }

    protected override DbParameter GetParameter(int index)
    {
        return (this._parameters[index] as DbParameter)!;
    }

    protected override DbParameter GetParameter(string parameterName)
    {
        throw new NotImplementedException();
    }

    protected override void SetParameter(int index, DbParameter value)
    {
        this._parameters[index] = value;
    }

    protected override void SetParameter(string parameterName, DbParameter value)
    {
        throw new NotImplementedException();
    }
}
