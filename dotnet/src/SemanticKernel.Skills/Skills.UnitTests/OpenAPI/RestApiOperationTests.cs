// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Net.Http;
using System.Web;
using Microsoft.SemanticKernel.Skills.OpenAPI.Model;
using Microsoft.SemanticKernel.Skills.OpenAPI.Rest;
using Xunit;

namespace SemanticKernel.Skills.UnitTests.OpenAPI;

public class RestApiOperationTests
{
    [Fact]
    public void ItShouldRenderHeaderValuesFromArguments()
    {
        //Arrange
        var rawHeaders = new Dictionary<string, string>();
        rawHeaders.Add("fake_header_one", string.Empty);
        rawHeaders.Add("fake_header_two", string.Empty);

        var arguments = new Dictionary<string, string>();
        arguments.Add("fake_header_one", "fake_header_one_value");
        arguments.Add("fake_header_two", "fake_header_two_value");

        var sut = new RestApiOperation("fake_id", "fake_url", "fake_path", HttpMethod.Get, "fake_description", new List<RestApiOperationParameter>(),
            rawHeaders);

        //Act
        var headers = sut.RenderHeaders(arguments);

        //Assert
        Assert.Equal(2, headers.Count);

        var headerOne = headers["fake_header_one"];
        Assert.Equal("fake_header_one_value", headerOne);

        var headerTwo = headers["fake_header_two"];
        Assert.Equal("fake_header_two_value", headerTwo);
    }

    [Fact]
    public void ItShouldUseHeaderValuesIfTheyAreAlreadySupplied()
    {
        //Arrange
        var rawHeaders = new Dictionary<string, string>();
        rawHeaders.Add("fake_header_one", "fake_header_one_value");
        rawHeaders.Add("fake_header_two", "fake_header_two_value");

        var sut = new RestApiOperation("fake_id", "fake_url", "fake_path", HttpMethod.Get, "fake_description", new List<RestApiOperationParameter>(),
            rawHeaders);

        //Act
        var headers = sut.RenderHeaders(new Dictionary<string, string>());

        //Assert
        Assert.Equal(2, headers.Count);

        var headerOne = headers["fake_header_one"];
        Assert.Equal("fake_header_one_value", headerOne);

        var headerTwo = headers["fake_header_two"];
        Assert.Equal("fake_header_two_value", headerTwo);
    }

    [Fact]
    public void ItShouldThrowExceptionIfHeadersHaveNoValuesAndHeadersMetadataNotSupplied()
    {
        //Arrange
        var rawHeaders = new Dictionary<string, string>();
        rawHeaders.Add("fake_header_one", string.Empty);
        rawHeaders.Add("fake_header_two", string.Empty);

        var metadata = new List<RestApiOperationParameter>();

        var sut = new RestApiOperation("fake_id", "fake_url", "fake_path", HttpMethod.Get, "fake_description", metadata, rawHeaders);

        //Act
        void act() => sut.RenderHeaders(new Dictionary<string, string>());

        //assert
        Assert.Throws<RestApiOperationException>(act);
    }

    [Fact]
    public void ItShouldThrowExceptionIfHeadersHaveNoValuesAndSomeHeadersAreRequired()
    {
        //Arrange
        var rawHeaders = new Dictionary<string, string>();
        rawHeaders.Add("fake_header_one", string.Empty);
        rawHeaders.Add("fake_header_two", string.Empty);

        var metadata = new List<RestApiOperationParameter>();
        metadata.Add(new RestApiOperationParameter("fake_header_one", "string", true, RestApiOperationParameterLocation.Header,
            RestApiOperationParameterStyle.Simple));
        metadata.Add(new RestApiOperationParameter("fake_header_two", "string", false, RestApiOperationParameterLocation.Header,
            RestApiOperationParameterStyle.Simple));

        var sut = new RestApiOperation("fake_id", "fake_url", "fake_path", HttpMethod.Get, "fake_description", metadata, rawHeaders);

        //Act
        void act() => sut.RenderHeaders(new Dictionary<string, string>());

        //assert
        Assert.Throws<RestApiOperationException>(act);
    }

    [Fact]
    public void ItShouldSkipNotRequiredHeaderHavingNeitherValueNorDefaultValue()
    {
        //Arrange
        var rawHeaders = new Dictionary<string, string>();
        rawHeaders.Add("fake_header_one", string.Empty);
        rawHeaders.Add("fake_header_two", string.Empty);

        var metadata = new List<RestApiOperationParameter>();
        metadata.Add(new RestApiOperationParameter("fake_header_one", "string", true, RestApiOperationParameterLocation.Header,
            RestApiOperationParameterStyle.Simple));
        metadata.Add(new RestApiOperationParameter("fake_header_two", "string", false, RestApiOperationParameterLocation.Header,
            RestApiOperationParameterStyle.Simple));

        var arguments = new Dictionary<string, string>();
        arguments.Add("fake_header_one", "fake_header_one_value");

        var sut = new RestApiOperation("fake_id", "fake_url", "fake_path", HttpMethod.Get, "fake_description", metadata, rawHeaders);

        //Act
        var headers = sut.RenderHeaders(arguments);

        //Assert
        Assert.Equal(1, headers.Count);

        var headerOne = headers["fake_header_one"];
        Assert.Equal("fake_header_one_value", headerOne);
    }

    [Fact]
    public void ItShouldUseParameterDefaultValueForNotRequiredHeaderAndIfValueNotSupplied()
    {
        //Arrange
        var rawHeaders = new Dictionary<string, string>();
        rawHeaders.Add("fake_header_one", string.Empty);
        rawHeaders.Add("fake_header_two", string.Empty);

        var metadata = new List<RestApiOperationParameter>();
        metadata.Add(new RestApiOperationParameter("fake_header_one", "string", true, RestApiOperationParameterLocation.Header,
            RestApiOperationParameterStyle.Simple));
        metadata.Add(new RestApiOperationParameter("fake_header_two", "string", false, RestApiOperationParameterLocation.Header,
            RestApiOperationParameterStyle.Simple, defaultValue: "fake_header_two_default_value"));

        var arguments = new Dictionary<string, string>();
        arguments.Add("fake_header_one", "fake_header_one_value"); //Argument is only provided for the first parameter and not for the second one

        var sut = new RestApiOperation("fake_id", "fake_url", "fake_path", HttpMethod.Get, "fake_description", metadata, rawHeaders);

        //Act
        var headers = sut.RenderHeaders(arguments);

        //Assert
        Assert.Equal(2, headers.Count);

        var headerOne = headers["fake_header_one"];
        Assert.Equal("fake_header_one_value", headerOne);

        var headerTwo = headers["fake_header_two"];
        Assert.Equal("fake_header_two_default_value", headerTwo);
    }

    [Fact]
    public void ItShouldNotWrapQueryStringValuesOfStringTypeIntoSingleQuotes()
    {
        //Arrange
        var metadata = new List<RestApiOperationParameter>();
        metadata.Add(new RestApiOperationParameter("fake_query_string_param", "string", false, RestApiOperationParameterLocation.Query,
            RestApiOperationParameterStyle.Simple));

        var arguments = new Dictionary<string, string>();
        arguments.Add("fake_query_string_param", "fake_query_string_param_value");

        var sut = new RestApiOperation("fake_id", "https://fake-random-test-host", "fake_path", HttpMethod.Get, "fake_description", metadata,
            new Dictionary<string, string>());

        //Act
        var url = sut.BuildOperationUrl(arguments);

        //Assert
        Assert.NotNull(url);

        var parameterValue = HttpUtility.ParseQueryString(url.Query)["fake_query_string_param"];
        Assert.NotNull(parameterValue);
        Assert.Equal("fake_query_string_param_value", parameterValue); // Making sure that query string value of string type is not wrapped with quotes.
    }

    [Theory]
    [InlineData(":", "%3a")]
    [InlineData("/", "%2f")]
    [InlineData("?", "%3f")]
    [InlineData("#", "%23")]
    public void ItShouldEncodeSpecialSymbolsInQueryStringValues(string specialSymbol, string encodedEquivalent)
    {
        //Arrange
        var metadata = new List<RestApiOperationParameter>();
        metadata.Add(new RestApiOperationParameter("fake_query_param", "string", false, RestApiOperationParameterLocation.Query,
            RestApiOperationParameterStyle.Simple));

        var arguments = new Dictionary<string, string>();
        arguments.Add("fake_query_param", $"fake_query_param_value{specialSymbol}");

        var sut = new RestApiOperation("fake_id", "https://fake-random-test-host", "fake_path", HttpMethod.Get, "fake_description", metadata,
            new Dictionary<string, string>());

        //Act
        var url = sut.BuildOperationUrl(arguments);

        //Assert
        Assert.NotNull(url);

        Assert.EndsWith(encodedEquivalent, url.OriginalString, System.StringComparison.InvariantCulture);
    }
}
