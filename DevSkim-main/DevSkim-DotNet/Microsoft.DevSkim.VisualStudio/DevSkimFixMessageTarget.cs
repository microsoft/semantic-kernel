namespace Microsot.DevSkim.LanguageClient
{
    using Microsoft.DevSkim.LanguageProtoInterop;
    using Microsoft.DevSkim.VisualStudio;
    using Newtonsoft.Json.Linq;
    using StreamJsonRpc;
    using System;
    using System.Collections.Concurrent;
    using System.Collections.Generic;
    using System.Threading.Tasks;

    public class DevSkimFixMessageTarget
    {
        public DevSkimFixMessageTarget()
        {
        }

        /// <summary>
        /// Remove all Code fixes for the specified filename that are not of the specified version
        /// </summary>
        /// <param name="token">JToken representation of <see cref="MappingsVersion"/></param>
        /// <returns></returns>
        [JsonRpcMethod(DevSkimMessages.FileVersion)]
        public async Task RemoveOldMappingsByVersionAsync(JToken token)
        {
            await Task.Run(() =>
            {
                MappingsVersion version = token.ToObject<MappingsVersion>();
                if (version is { })
                {
                    if (StaticData.FileToCodeFixMap.ContainsKey(version.fileName))
                    {
                        foreach (var key in StaticData.FileToCodeFixMap[version.fileName].Keys)
                        {
                            if (key != version.version)
                            {
                                StaticData.FileToCodeFixMap[version.fileName].TryRemove(key, out _);
                            }
                        }
                    }
                }
            });
        }


        /// <summary>
        /// Update the client cache of available fixes for published diagnostics
        /// </summary>
        /// <param name="jToken">JToken representation of <see cref="CodeFixMapping"/></param>
        /// <returns></returns>
        [JsonRpcMethod(DevSkimMessages.CodeFixMapping)]
        public async Task CodeFixMappingEventAsync(JToken jToken)
        {
            await Task.Run(() =>
            {
                CodeFixMapping mapping = jToken.ToObject<CodeFixMapping>();
                if (mapping is { })
                {
                    StaticData.FileToCodeFixMap.AddOrUpdate(mapping.fileName,
                    // Add New Nested Dictionary
                    (Uri _) => new (new Dictionary<int, ConcurrentDictionary<CodeFixMapping, bool>> 
                    { { mapping.version ?? -1, new (new Dictionary<CodeFixMapping, bool>() 
                        { {mapping, true } }) } }),
                    // Update Nested Dictionary
                    (key, oldValue) =>
                    {
                        oldValue.AddOrUpdate(mapping.version ?? -1,
                            // Add new Set of mappings
                            (int _) =>
                            {
                                var addedMapping = new ConcurrentDictionary<CodeFixMapping, bool>();
                                addedMapping.TryAdd(mapping, true);
                                return addedMapping;
                            },
                            // Update Set of CodeFixMappings
                            (versionKey, oldSet) => { oldSet.TryAdd(mapping, true); return oldSet; });
                        return oldValue;
                    });
                }
            });
        }
    }
}