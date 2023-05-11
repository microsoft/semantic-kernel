package com.microsoft.semantickernel;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.Properties;

public class Config {
  public static String getOpenAIKey(String conf) {
    return getConfigValue(conf, "token");
  }

  public static String getAzureOpenAIEndpoint(String conf) {
    return getConfigValue(conf, "endpoint");
  }

  private static String getConfigValue(String configFile, String propertyName) {
    File config = new File(configFile);
    try (FileInputStream fis = new FileInputStream(config.getAbsolutePath())) {
      Properties props = new Properties();
      props.load(fis);
      return props.getProperty(propertyName);
    } catch (IOException e) {
      throw new RuntimeException(configFile + " not configured properly");
    }
  }
}
