// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector;

/// <summary>
/// The goal of this class is to be able to progressively alter some input settings by cloning them just once if needed and none if no change is applied
/// </summary>
/// <typeparam name="T">The type of the settings to update</typeparam>
public class SettingsUpdater<T>
{
    private readonly T _settings;
    private readonly Func<T, T> _cloneFunc;
    private T _modifiedSettings;
    private bool _isModified;

    public SettingsUpdater(T settings, Func<T, T> cloneFunc)
    {
        this._settings = settings;
        this._cloneFunc = cloneFunc;
        this._isModified = false;
        this._modifiedSettings = settings;
    }

    public T ModifyIfChanged<TValue>(Func<T, TValue> selector, Func<TValue, TValue> transform, Action<T, TValue> setter, out bool changed)
    {
        var oldValue = selector(this._settings);
        var newValue = transform(oldValue);
        if (!EqualityComparer<TValue>.Default.Equals(oldValue, newValue))
        {
            changed = true;
            if (!this._isModified)
            {
                this._modifiedSettings = this._cloneFunc(this._settings);
                this._isModified = true;
            }

            setter(this._modifiedSettings, newValue);
        }
        else
        {
            changed = false;
        }

        return this._modifiedSettings;
    }
}
