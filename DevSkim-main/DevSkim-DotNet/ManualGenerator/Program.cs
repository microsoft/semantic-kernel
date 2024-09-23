﻿namespace ManualGenerator
{
    using Microsoft.DevSkim.LanguageProtoInterop;
    using System.Text;

    /// <summary>
    /// Run this to generate the update settinsg method for all implemented settings
    /// </summary>
    internal class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine(Execute());
        }

        public static string Execute()
        {
            StringBuilder source = new StringBuilder();
            source.Append($@"// <auto-generated/>
    namespace Microsoft.DevSkim.VisualStudio
    {{
        using System;
        using Microsoft.DevSkim.LanguageProtoInterop;
        using System.Collections.Generic;

        internal partial class VisualStudioSettingsManager
        {{
            partial void UpdateSettings(string propertyName)
            {{
                switch(propertyName)
                {{
");

            string baseIndentation = "                ";
            var props = typeof(IDevSkimOptions).GetProperties().Select(x => (x.Name, x.PropertyType));
            foreach (var prop in props)
            {
                var typeNameString = GetTypeNameString(prop.PropertyType);
                source.Append($@"{baseIndentation}case ""{prop.Name}"":
                        {{
                            var res = Get<{typeNameString}>(propertyName);
                            if (res.Item1 == ValueResultEnum.Success)
                            {{
                                _currentSettings.{prop.Name} = res.Item2{ConditionallyUseNullCoalescing(typeNameString)}
                            }}
                            break;
                        }}                    
");
            }

            source.Append($@"{baseIndentation}default: break;
                }}
            }}
        }}
    }}");
            return source.ToString();
        }

        private static string ConditionallyUseNullCoalescing(string typeNameString)
        {
            return typeNameString.StartsWith("List") ? $" ?? new {typeNameString}();" : ";";
        }

        private static string GetTypeNameString(Type propPropertyType)
        {
            return propPropertyType.Name switch
            {
                "String" => "string",
                "List`1" => $"List<{GetTypeNameString(propPropertyType.GetGenericArguments()[0])}>",
                "Boolean" => "bool",
                "Int32" => "int",
                "CommentStylesEnum" => "CommentStylesEnum",
                _ => "string"
            };
        }
    }
}