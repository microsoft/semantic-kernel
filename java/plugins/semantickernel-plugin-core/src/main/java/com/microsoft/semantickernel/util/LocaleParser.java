// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.util;

import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionParameters;
import java.util.Locale;

/**
 * Locale parser to support Java 8 and Java 9+ due to JEP 252.
 *
 * <p>Supports parsing strings containing languageCode_countryCode and languageCode-countryCode
 * styles.
 */
public final class LocaleParser {

    private LocaleParser() {}

    /**
     * Parses the locale. If the input is "en-US", it will return a Locale based on the language
     * tag. If the input is "en_US", it will return a Locale based on the language and country code.
     * Otherwise, it will return a Locale based on the input.
     *
     * <p>'en' 'US' used as example above.
     *
     * @param locale the locale in String text.
     * @return
     */
    public static final Locale parseLocale(String locale) {
        Locale parsedLocale = null;

        if (locale == null
                || "".equals(locale.trim())
                || SKFunctionParameters.NO_DEFAULT_VALUE.equals(locale)) {
            return Locale.getDefault();
        } else if (locale.indexOf("-") > -1) {
            parsedLocale = Locale.forLanguageTag(locale);
        } else if (locale.indexOf("_") > -1) {
            String[] parts = locale.split("_");
            parsedLocale = new Locale(parts[0], parts[1]);
        } else {
            parsedLocale = new Locale(locale);
        }

        return parsedLocale;
    }
}
