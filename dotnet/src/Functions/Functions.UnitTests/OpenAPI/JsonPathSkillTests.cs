// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Functions.OpenAPI;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.OpenAPI;

public class JsonPathSkillTests
{
    private const string Json = @"{
  'Stores': [
    'Lambton Quay',
    'Willis Street'
  ],
  'Manufacturers': [
    {
      'Name': 'Acme Co',
      'Products': [
        {
          'Name': 'Anvil',
          'Price': 50
        }
      ]
    },
    {
      'Name': 'Contoso',
      'Products': [
        {
          'Name': 'Elbow Grease',
          'Price': 99.95
        },
        {
          'Name': 'Headlight Fluid',
          'Price': 4
        }
      ]
    }
  ]
}";

    [Theory]
    [InlineData("$.Manufacturers[0].Products[0].Name", "Anvil")] // single value
    [InlineData("$.Manufacturers[0].Products[0].Foo", "")] // no value
    public void GetJsonElementValueSucceeds(string jsonPath, string expected)
    {
        var target = new JsonPathPlugin();

        string actual = target.GetJsonElementValue(Json, jsonPath);

        Assert.Equal(expected, actual, StringComparer.OrdinalIgnoreCase);
    }

    [Theory]
    [InlineData("$..Products[?(@.Price >= 50)].Name", "[\"Anvil\",\"Elbow Grease\"]")] // multiple values
    [InlineData("$.Manufacturers",
        "[[{\"Name\":\"Acme Co\",\"Products\":[{\"Name\":\"Anvil\",\"Price\":50}]},{\"Name\":\"Contoso\",\"Products\":[{\"Name\":\"Elbow Grease\",\"Price\":99.95},{\"Name\":\"Headlight Fluid\",\"Price\":4}]}]]")] // complex value
    public void GetJsonPropertyValueSucceeds(string jsonPath, string expected)
    {
        var target = new JsonPathPlugin();

        string actual = target.GetJsonElements(Json, jsonPath);

        Assert.Equal(expected, actual, StringComparer.OrdinalIgnoreCase);
    }
}
