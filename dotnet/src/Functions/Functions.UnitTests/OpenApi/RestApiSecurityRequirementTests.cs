// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.OpenApi;

public class RestApiSecurityRequirementTests
{
    [Fact]
    public void ItShouldWorkAsInstance()
    {
        // Arrange
        RestApiSecurityRequirement sut = [];

        RestApiSecurityScheme scheme = new();

        IList<string> scopes = ["scope"];

        // Act & Assert

        // Add
        sut.Add(scheme, scopes);
        Assert.Single(sut);

        // Remove
        sut.Remove(scheme);
        Assert.Empty(sut);

        // Clear
        sut.Add(scheme, scopes);
        sut.Clear();
        Assert.Empty(sut);

        // ContainsKey
        sut.Add(scheme, scopes);
        Assert.True(sut.ContainsKey(scheme));

        // TryGetValue
        Assert.True(sut.TryGetValue(scheme, out IList<string>? value) && object.Equals(value, scopes));

        // this[RestApiSecurityScheme key]
        IList<string> newScopes = ["scope1"];
        sut[scheme] = newScopes;
        Assert.Equal(newScopes, sut[scheme]);

        // Keys
        Assert.Single(sut.Keys);
        Assert.Equal(scheme, sut.Keys.ElementAt(0));

        // Values
        Assert.Single(sut.Values);
        Assert.Equal(newScopes, sut.Values.ElementAt(0));

        // Freese
        sut.Freeze();
        Assert.Throws<InvalidOperationException>(() => sut.Add(scheme, scopes));
        Assert.Throws<InvalidOperationException>(() => sut.Remove(scheme));
        Assert.Throws<InvalidOperationException>(sut.Clear);
        Assert.Throws<InvalidOperationException>(() => sut[scheme] = scopes);
    }

    [Fact]
    public void ItShouldSupportAllMembersOfIDictionaryInterface()
    {
        // Arrange
        RestApiSecurityRequirement instance = [];

        IDictionary<RestApiSecurityScheme, IList<string>> sut = instance;

        RestApiSecurityScheme scheme = new();

        IList<string> scopes = ["scope"];

        // Act & Assert

        // Add
        sut.Add(scheme, scopes);
        Assert.Single(sut);

        // Remove
        sut.Remove(scheme);
        Assert.Empty(sut);

        // ContainsKey
        sut.Add(scheme, scopes);
        Assert.True(sut.ContainsKey(scheme));

        // TryGetValue
        Assert.True(sut.TryGetValue(scheme, out IList<string>? value) && object.Equals(value, scopes));

        // this[RestApiSecurityScheme key]
        IList<string> newScopes = ["scope1"];
        sut[scheme] = newScopes;
        Assert.Equal(newScopes, sut[scheme]);

        // Keys
        Assert.Single(sut.Keys);
        Assert.Equal(scheme, sut.Keys.ElementAt(0));

        // Values
        Assert.Single(sut.Values);
        Assert.Equal(newScopes, sut.Values.ElementAt(0));

        // Freese
        instance.Freeze();
        Assert.Throws<InvalidOperationException>(() => sut.Add(scheme, scopes));
        Assert.Throws<InvalidOperationException>(() => sut.Remove(scheme));
        Assert.Throws<InvalidOperationException>(() => sut[scheme] = scopes);
    }

    [Fact]
    public void ItShouldSupportAllMembersOfIReadOnlyDictionaryInterface()
    {
        // Arrange
        RestApiSecurityRequirement instance = [];

        IReadOnlyDictionary<RestApiSecurityScheme, IList<string>> sut = instance;

        RestApiSecurityScheme scheme = new();

        IList<string> scopes = ["scope"];

        // Act & Assert
        instance.Add(scheme, scopes);
        Assert.Single(sut);

        // ContainsKey
        Assert.True(sut.ContainsKey(scheme));

        // TryGetValue
        Assert.True(sut.TryGetValue(scheme, out IList<string>? value) && object.Equals(value, scopes));

        // this[RestApiSecurityScheme key]
        Assert.Equal(scopes, sut[scheme]);

        // Keys
        Assert.Single(sut.Keys);
        Assert.Equal(scheme, sut.Keys.ElementAt(0));

        // Values
        Assert.Single(sut.Values);
        Assert.Equal(scopes, sut.Values.ElementAt(0));
    }

    [Fact]
    public void ItShouldSupportAllMembersOfICollectionInterface()
    {
        // Arrange
        RestApiSecurityRequirement instance = [];

        ICollection<KeyValuePair<RestApiSecurityScheme, IList<string>>> sut = instance;

        RestApiSecurityScheme scheme = new();

        IList<string> scopes = ["scope"];

        KeyValuePair<RestApiSecurityScheme, IList<string>> keyValuePair = new(scheme, scopes);

        // Act & Assert

        // Add
        sut.Add(keyValuePair);

        // Count
#pragma warning disable xUnit2013 // Do not use equality check to check for collection size.
        Assert.Equal(1, sut.Count);
#pragma warning restore xUnit2013 // Do not use equality check to check for collection size.

        // Remove
        sut.Remove(keyValuePair);
        Assert.Empty(sut);

        // Contains
        sut.Add(keyValuePair);
        Assert.True(sut.Contains(keyValuePair));

        // Clear
        sut.Clear();

        // IsReadOnly
        Assert.False(sut.IsReadOnly);

        // CopyTo
        sut.Add(keyValuePair);
        KeyValuePair<RestApiSecurityScheme, IList<string>>[] array = new KeyValuePair<RestApiSecurityScheme, IList<string>>[1];
        sut.CopyTo(array, 0);
        Assert.Equal(keyValuePair, array[0]);

        // Freese
        instance.Freeze();
        Assert.True(sut.IsReadOnly);

        Assert.Throws<InvalidOperationException>(() => sut.Add(new KeyValuePair<RestApiSecurityScheme, IList<string>>()));
        Assert.Throws<InvalidOperationException>(() => sut.Remove(keyValuePair));
        Assert.Throws<InvalidOperationException>(sut.Clear);
    }

    [Fact]
    public void ItShouldSupportAllMembersOfIEnumerableInterface()
    {
        // Arrange
        RestApiSecurityScheme scheme = new();

        IList<string> scopes = ["scope"];

        RestApiSecurityRequirement instance = [];
        instance.Add(scheme, scopes);

        IEnumerable<KeyValuePair<RestApiSecurityScheme, IList<string>>> sut = instance;

        // Act & Assert

        var enumerator = sut.GetEnumerator();

        Assert.True(enumerator.MoveNext());
        Assert.Equal(instance.ElementAt(0), enumerator.Current);
        Assert.False(enumerator.MoveNext());
    }

    [Fact]
    public void ItShouldFreezeKeysAndValues()
    {
        // Arrange
        RestApiOAuthFlows flows = new()
        {
            Implicit = new RestApiOAuthFlow() { Scopes = new Dictionary<string, string>() { ["s1"] = "v1" } },
            Password = new RestApiOAuthFlow() { Scopes = new Dictionary<string, string>() { ["s1"] = "v1" } },
            ClientCredentials = new RestApiOAuthFlow() { Scopes = new Dictionary<string, string>() { ["s1"] = "v1" } },
            AuthorizationCode = new RestApiOAuthFlow() { Scopes = new Dictionary<string, string>() { ["s1"] = "v1" } },
        };

        RestApiSecurityScheme scheme = new() { Flows = flows };

        RestApiSecurityRequirement sut = [];
        sut.Add(scheme, ["scope"]);

        // Act
        sut.Freeze();

        // Assert
        Assert.Throws<NotSupportedException>(() => scheme.Flows.Implicit.Scopes.Add("scope-name", "scope-description"));
        Assert.Throws<NotSupportedException>(() => scheme.Flows.Implicit.Scopes["scope-name"] = "scope-description");

        Assert.Throws<NotSupportedException>(() => scheme.Flows.Password.Scopes.Add("scope-name", "scope-description"));
        Assert.Throws<NotSupportedException>(() => scheme.Flows.Password.Scopes["scope-name"] = "scope-description");

        Assert.Throws<NotSupportedException>(() => scheme.Flows.ClientCredentials.Scopes.Add("scope-name", "scope-description"));
        Assert.Throws<NotSupportedException>(() => scheme.Flows.ClientCredentials.Scopes["scope-name"] = "scope-description");

        Assert.Throws<NotSupportedException>(() => scheme.Flows.AuthorizationCode.Scopes.Add("scope-name", "scope-description"));
        Assert.Throws<NotSupportedException>(() => scheme.Flows.AuthorizationCode.Scopes["scope-name"] = "scope-description");

        Assert.Throws<NotSupportedException>(() => sut[scheme].Add("new-scheme"));
        Assert.Throws<InvalidOperationException>(() => sut[scheme] = []);
    }
}
