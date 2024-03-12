# Changelog

[PyPI History][1]

[1]: https://pypi.org/project/google-auth/#history

## [2.17.3](https://github.com/googleapis/google-auth-library-python/compare/v2.17.2...v2.17.3) (2023-04-12)


### Bug Fixes

* Add useEmailAzp claim for id token iam flow ([#1270](https://github.com/googleapis/google-auth-library-python/issues/1270)) ([7a9c6f2](https://github.com/googleapis/google-auth-library-python/commit/7a9c6f2d90688e57583437c0872eb12dc5b0d833))

## [2.17.2](https://github.com/googleapis/google-auth-library-python/compare/v2.17.1...v2.17.2) (2023-04-05)


### Bug Fixes

* Do not create new JWT credentials if they make the same claims as the existing. ([#1267](https://github.com/googleapis/google-auth-library-python/issues/1267)) ([eebb7b6](https://github.com/googleapis/google-auth-library-python/commit/eebb7b6630a7fc1e943a4d5f8fc76e9dd6dbe687))

## [2.17.1](https://github.com/googleapis/google-auth-library-python/compare/v2.17.0...v2.17.1) (2023-03-30)


### Bug Fixes

* Print out reauth plugin error and raise if challenge output is None ([#1265](https://github.com/googleapis/google-auth-library-python/issues/1265)) ([08d22fe](https://github.com/googleapis/google-auth-library-python/commit/08d22fe805e0401c3a902ce96f9c3797e7f166b1))

## [2.17.0](https://github.com/googleapis/google-auth-library-python/compare/v2.16.3...v2.17.0) (2023-03-28)


### Features

* Experimental service account iam endpoint flow for id token ([#1258](https://github.com/googleapis/google-auth-library-python/issues/1258)) ([8ff0de5](https://github.com/googleapis/google-auth-library-python/commit/8ff0de5f6c26c8778e24e57d6b7f449856357f81))


### Bug Fixes

* Python: Remove aws url validation ([#1254](https://github.com/googleapis/google-auth-library-python/issues/1254)) ([20a966b](https://github.com/googleapis/google-auth-library-python/commit/20a966bbbfc66932f471e0bfd191769f40332233))

## [2.16.3](https://github.com/googleapis/google-auth-library-python/compare/v2.16.2...v2.16.3) (2023-03-24)


### Bug Fixes

* Read both applicationId and relyingPartyId. ([#1246](https://github.com/googleapis/google-auth-library-python/issues/1246)) ([e125dfe](https://github.com/googleapis/google-auth-library-python/commit/e125dfe1e345bf5f6cef4efee8215de129401c51))

## [2.16.2](https://github.com/googleapis/google-auth-library-python/compare/v2.16.1...v2.16.2) (2023-03-02)


### Bug Fixes

* Call gcloud config get project to get project for user cred ([#1243](https://github.com/googleapis/google-auth-library-python/issues/1243)) ([c078a13](https://github.com/googleapis/google-auth-library-python/commit/c078a13f3d7a6bda69efab11f11c1120e20137ef))
* Do not use hardcoded string 'python', when you mean sys.executable. ([#1233](https://github.com/googleapis/google-auth-library-python/issues/1233)) ([91ac8e6](https://github.com/googleapis/google-auth-library-python/commit/91ac8e66396fd2335f2be6e7b40dc5c4f6e47bc2))
* Don't retry if error or error_description is not string ([#1241](https://github.com/googleapis/google-auth-library-python/issues/1241)) ([e2d263a](https://github.com/googleapis/google-auth-library-python/commit/e2d263a2e79a35e8cc90aa338780d07c3313dc76))
* Improve ADC related errors and warnings ([#1237](https://github.com/googleapis/google-auth-library-python/issues/1237)) ([2dfa213](https://github.com/googleapis/google-auth-library-python/commit/2dfa21371185340404d5d739723a8cd434886e02))

## [2.16.1](https://github.com/googleapis/google-auth-library-python/compare/v2.16.0...v2.16.1) (2023-02-17)


### Bug Fixes

* Add support for python 3.11 ([#1212](https://github.com/googleapis/google-auth-library-python/issues/1212)) ([1fc95e3](https://github.com/googleapis/google-auth-library-python/commit/1fc95e3c3ecfbceb16c1be28725e8bc9eefe8bb0))
* Remove 3PI config url validation ([#1220](https://github.com/googleapis/google-auth-library-python/issues/1220)) ([8b95515](https://github.com/googleapis/google-auth-library-python/commit/8b95515718d50b028c43ea9d6a7220489ffb5da0))
* Update the docs generator interpreter to unblock documentation build ([#1218](https://github.com/googleapis/google-auth-library-python/issues/1218)) ([9d36c2f](https://github.com/googleapis/google-auth-library-python/commit/9d36c2f1f9e1eac8fbff4be504986dff5e7d4da2))

## [2.16.0](https://github.com/googleapis/google-auth-library-python/compare/v2.15.0...v2.16.0) (2023-01-09)


### Features

* AwsCredentials should not call metadata server if security creds and region are retrievable through the environment variables ([#1195](https://github.com/googleapis/google-auth-library-python/issues/1195)) ([5e27c8f](https://github.com/googleapis/google-auth-library-python/commit/5e27c8f213b2e19ec504a04e1f95fc1333ea9e1e))
* Wrap all python built-in exceptions into library excpetions ([#1191](https://github.com/googleapis/google-auth-library-python/issues/1191)) ([a83af39](https://github.com/googleapis/google-auth-library-python/commit/a83af399fe98764ee851997bf3078ec45a9b51c9))


### Bug Fixes

* Allow get_project_id to take a request ([#1203](https://github.com/googleapis/google-auth-library-python/issues/1203)) ([9a4d23a](https://github.com/googleapis/google-auth-library-python/commit/9a4d23a28eb4b9aa9e457ad053c087a0450eb298))
* Make OAUTH2.0 client resistant to string type 'expires_in' responses from non-compliant services ([#1208](https://github.com/googleapis/google-auth-library-python/issues/1208)) ([9fc7b1c](https://github.com/googleapis/google-auth-library-python/commit/9fc7b1c5613366cc1ad7186f894cec26a5f2231e))

## [2.15.0](https://github.com/googleapis/google-auth-library-python/compare/v2.14.1...v2.15.0) (2022-12-01)


### Features

* Add api_key credentials ([#1184](https://github.com/googleapis/google-auth-library-python/issues/1184)) ([370293e](https://github.com/googleapis/google-auth-library-python/commit/370293e84a14af0d6c6b34287bdcad020e0580e4))
* Introduce a way to provide scopes granted by user ([#1189](https://github.com/googleapis/google-auth-library-python/issues/1189)) ([189f504](https://github.com/googleapis/google-auth-library-python/commit/189f504cbdfe043949688dfe55f3f449befad991))


### Bug Fixes

* Allow mtls sts endpoint for external account token urls. ([#1185](https://github.com/googleapis/google-auth-library-python/issues/1185)) ([c86dd69](https://github.com/googleapis/google-auth-library-python/commit/c86dd69cf79809e2d532a745a236db840fd8bc5d))
* CI broken by removal of py.path ([#1194](https://github.com/googleapis/google-auth-library-python/issues/1194)) ([f719415](https://github.com/googleapis/google-auth-library-python/commit/f719415475e10e5af9ec75b3b13c57c25682bea0))
* Ensure JWT segments have the right types ([#1162](https://github.com/googleapis/google-auth-library-python/issues/1162)) ([fc843cd](https://github.com/googleapis/google-auth-library-python/commit/fc843cd318e4ac4f40cf83bbcd7c6eae2b597ff8))
* Updated the lower bound of interactive timeout and fix the kwarg… ([#1182](https://github.com/googleapis/google-auth-library-python/issues/1182)) ([50c0fd2](https://github.com/googleapis/google-auth-library-python/commit/50c0fd29a3b6a4fd6dc4b801d883f5d2b6de88c6))

## [2.14.1](https://github.com/googleapis/google-auth-library-python/compare/v2.14.0...v2.14.1) (2022-11-07)


### Bug Fixes

* Apply quota project for compute cred in adc ([#1177](https://github.com/googleapis/google-auth-library-python/issues/1177)) ([b9aa92a](https://github.com/googleapis/google-auth-library-python/commit/b9aa92a1f1640f9c8bc4beb7b13051a01cb263a4))
* Update minimum required version of cryptography in pyopenssl extra ([#1176](https://github.com/googleapis/google-auth-library-python/issues/1176)) ([e9e76d1](https://github.com/googleapis/google-auth-library-python/commit/e9e76d1ee4e4b39edcd6821ced7a5bc3ed60eba0))
* Validate url domain for aws metadata urls ([#1174](https://github.com/googleapis/google-auth-library-python/issues/1174)) ([f9d7d77](https://github.com/googleapis/google-auth-library-python/commit/f9d7d77739db86870c9b87b003e8ce0c93d53e53))

## [2.14.0](https://github.com/googleapis/google-auth-library-python/compare/v2.13.0...v2.14.0) (2022-10-31)


### Features

* Add token_info_url to external account credentials ([#1168](https://github.com/googleapis/google-auth-library-python/issues/1168)) ([9adee75](https://github.com/googleapis/google-auth-library-python/commit/9adee75712202234aa0b124a9ca0424654022428))
* Read Quota Project from Environment Variable ([#1163](https://github.com/googleapis/google-auth-library-python/issues/1163)) ([57b3e42](https://github.com/googleapis/google-auth-library-python/commit/57b3e424927a5d86fbab8b231109a5aae1233745))


### Bug Fixes

* Adding more properties to external_account_authorized_user ([#1169](https://github.com/googleapis/google-auth-library-python/issues/1169)) ([a12b96d](https://github.com/googleapis/google-auth-library-python/commit/a12b96dcfa7cb58d9171fd7f2a7ea8331a228419))

## [2.13.0](https://github.com/googleapis/google-auth-library-python/compare/v2.12.0...v2.13.0) (2022-10-14)


### Features

* Adds new external account authorized user credentials ([#1160](https://github.com/googleapis/google-auth-library-python/issues/1160)) ([523f811](https://github.com/googleapis/google-auth-library-python/commit/523f8117a72548d91f1bb169a3c91b095477ce3b))
* Implement pluggable auth interactive mode ([#1131](https://github.com/googleapis/google-auth-library-python/issues/1131)) ([44a189f](https://github.com/googleapis/google-auth-library-python/commit/44a189fc6185bf33e9d5609cf8d57a846cd98aaf))
* Introduce the functionality to override token_uri in credentials ([#1159](https://github.com/googleapis/google-auth-library-python/issues/1159)) ([73bc7e9](https://github.com/googleapis/google-auth-library-python/commit/73bc7e9e0e72b6c5057a13cdb4ac996b754ddb58))


### Bug Fixes

* Adding one more pattern to relax the regex check for sts and impersonation url endpoints ([#1158](https://github.com/googleapis/google-auth-library-python/issues/1158)) ([75326e3](https://github.com/googleapis/google-auth-library-python/commit/75326e397c619a2b58963d3fd9fc1a1a5eda13a0))

## [2.12.0](https://github.com/googleapis/google-auth-library-python/compare/v2.11.1...v2.12.0) (2022-09-26)


### Features

* Retry behavior ([#1113](https://github.com/googleapis/google-auth-library-python/issues/1113)) ([78d3790](https://github.com/googleapis/google-auth-library-python/commit/78d37906f0811f9878834ac34d5b83e5cbd58800))


### Bug Fixes

* Modify RefreshError exception to use gcloud ADC command. ([#1149](https://github.com/googleapis/google-auth-library-python/issues/1149)) ([059fd35](https://github.com/googleapis/google-auth-library-python/commit/059fd353d5f2a8527de8bf1fe6dbd5e326c0e29a))
* Revert "Update token refresh threshold from 20 seconds to 5 minutes". ([186464b](https://github.com/googleapis/google-auth-library-python/commit/186464bf5920fb3b76499ac542b0fb90023629de))

## [2.11.1](https://github.com/googleapis/google-auth-library-python/compare/v2.11.0...v2.11.1) (2022-09-20)


### Bug Fixes

* Fix socket leak in impersonated_credentials ([#1123](https://github.com/googleapis/google-auth-library-python/issues/1123)) ([b1eb467](https://github.com/googleapis/google-auth-library-python/commit/b1eb467f50f0c080e89a122426061b28f0be0567)), closes [#1122](https://github.com/googleapis/google-auth-library-python/issues/1122)
* Make pluggable auth tests work in all environments ([#1114](https://github.com/googleapis/google-auth-library-python/issues/1114)) ([bb5c979](https://github.com/googleapis/google-auth-library-python/commit/bb5c9791c64e2472a90ba7191f79f4c5fedb2538))
* Skip oauth2client adapter tests if oauth2client is not installed ([#1132](https://github.com/googleapis/google-auth-library-python/issues/1132)) ([d15092f](https://github.com/googleapis/google-auth-library-python/commit/d15092ff8b66b3039641d482a0debafde4ba0077))
* Update token refresh threshold from 20 seconds to 5 minutes ([#1146](https://github.com/googleapis/google-auth-library-python/issues/1146)) ([261a561](https://github.com/googleapis/google-auth-library-python/commit/261a56138fba33ff7d898ab5907a6098125fefef))


### Documentation

* **samples:** Add auth samples and tests ([#1102](https://github.com/googleapis/google-auth-library-python/issues/1102)) ([ac87520](https://github.com/googleapis/google-auth-library-python/commit/ac875201bc8ba5d638a9eafcd3ccfdeb73a2f0ec))

## [2.11.0](https://github.com/googleapis/google-auth-library-python/compare/v2.10.0...v2.11.0) (2022-08-18)


### Features

* add integration tests for configurable token lifespan ([#1103](https://github.com/googleapis/google-auth-library-python/issues/1103)) ([124bae6](https://github.com/googleapis/google-auth-library-python/commit/124bae60771a8984674a1d7eeab3ec22b2fa0033))


### Bug Fixes

* Async certificate retrieving ([#1101](https://github.com/googleapis/google-auth-library-python/issues/1101)) ([05f125d](https://github.com/googleapis/google-auth-library-python/commit/05f125def1205a14db52c870f2bfcef47f047206))

## [2.10.0](https://github.com/googleapis/google-auth-library-python/compare/v2.9.1...v2.10.0) (2022-08-05)


### Features

* add integration tests for pluggable auth ([#1073](https://github.com/googleapis/google-auth-library-python/issues/1073)) ([f8d776a](https://github.com/googleapis/google-auth-library-python/commit/f8d776a290270da8c43b0f5ba8e8a1fabfcf4dd3))
* support for configurable token lifetime ([0dc6a9a](https://github.com/googleapis/google-auth-library-python/commit/0dc6a9a30b994f20ad027bfc3715792aa97bd8af))
* support for configurable token lifetime ([#1079](https://github.com/googleapis/google-auth-library-python/issues/1079)) ([0dc6a9a](https://github.com/googleapis/google-auth-library-python/commit/0dc6a9a30b994f20ad027bfc3715792aa97bd8af))


### Bug Fixes

* async certificate decoding ([#1085](https://github.com/googleapis/google-auth-library-python/issues/1085)) ([741c6c6](https://github.com/googleapis/google-auth-library-python/commit/741c6c6f5e2d4e98cbae1e6c7a9bc128c6a97bae))
* Async system tests were not unwrapping async_generators ([#1086](https://github.com/googleapis/google-auth-library-python/issues/1086)) ([29d248a](https://github.com/googleapis/google-auth-library-python/commit/29d248acaf554c2bdba81c96999371c9e610c6b6))
* Fix IDTokenCredentials update bug ([#1072](https://github.com/googleapis/google-auth-library-python/issues/1072)) ([b62c25c](https://github.com/googleapis/google-auth-library-python/commit/b62c25ca408f72d86fda35b611edb3d2c6eb4f85))
* make expiration_time optional in response schema ([#1091](https://github.com/googleapis/google-auth-library-python/issues/1091)) ([032fb8d](https://github.com/googleapis/google-auth-library-python/commit/032fb8d1685a50081974ba85e6ead946f30a1ea8))
* refactor credential subclass parameters ([#1095](https://github.com/googleapis/google-auth-library-python/issues/1095)) ([8d15f69](https://github.com/googleapis/google-auth-library-python/commit/8d15f69711f38196934eabff5f05be26b3afcbf6))

## [2.9.1](https://github.com/googleapis/google-auth-library-python/compare/v2.9.0...v2.9.1) (2022-07-12)


### Bug Fixes

* there was a raise missing for throwing exceptions ([#1077](https://github.com/googleapis/google-auth-library-python/issues/1077)) ([d1f17b0](https://github.com/googleapis/google-auth-library-python/commit/d1f17b0ba71d90bff2402fde38bdbe51bc6481f9))

## [2.9.0](https://github.com/googleapis/google-auth-library-python/compare/v2.8.0...v2.9.0) (2022-06-28)


### Features

* pluggable auth support ([#1045](https://github.com/googleapis/google-auth-library-python/issues/1045)) ([de14f4e](https://github.com/googleapis/google-auth-library-python/commit/de14f4e855c081c08f14cb0211a06107e5314bf7))

## [2.8.0](https://github.com/googleapis/google-auth-library-python/compare/v2.7.0...v2.8.0) (2022-06-14)


### Features

* add experimental GDCH support ([#1044](https://github.com/googleapis/google-auth-library-python/issues/1044)) ([94fb5e2](https://github.com/googleapis/google-auth-library-python/commit/94fb5e27ef57b9ffb2fa58386bc0cb382ddafec2))

## [2.7.0](https://github.com/googleapis/google-auth-library-python/compare/v2.6.6...v2.7.0) (2022-06-07)


### Features

* add experimental enterprise cert support ([#1052](https://github.com/googleapis/google-auth-library-python/issues/1052)) ([dda7dda](https://github.com/googleapis/google-auth-library-python/commit/dda7ddaf859f5f7a21af714ebb422dfde4da46c8))
* add experimental GDCH support ([#1022](https://github.com/googleapis/google-auth-library-python/issues/1022)) ([5367aac](https://github.com/googleapis/google-auth-library-python/commit/5367aac881fdba814f66e4d6d5f59fccecc12547))
* Pluggable auth support ([#995](https://github.com/googleapis/google-auth-library-python/issues/995)) ([62daa73](https://github.com/googleapis/google-auth-library-python/commit/62daa73168f47806905bfc52b8f059995a193b71))


### Bug Fixes

* validate urls for external accounts ([#1031](https://github.com/googleapis/google-auth-library-python/issues/1031)) ([61b1f15](https://github.com/googleapis/google-auth-library-python/commit/61b1f1561ad6c3ddf4540143171351e53ff50f99))


### Reverts

* pluggable auth support [#995](https://github.com/googleapis/google-auth-library-python/issues/995) ([#1039](https://github.com/googleapis/google-auth-library-python/issues/1039)) ([513d999](https://github.com/googleapis/google-auth-library-python/commit/513d999d1f3b8a69bff86a2b91a73b6bdf6f92d0))
* revert experimental GDCH support ([#1022](https://github.com/googleapis/google-auth-library-python/issues/1022)) ([#1042](https://github.com/googleapis/google-auth-library-python/issues/1042)) ([c720995](https://github.com/googleapis/google-auth-library-python/commit/c720995aa08f539fe884685d9d53e599ca707e45))


### Documentation

* fix changelog header to consistent size ([#1046](https://github.com/googleapis/google-auth-library-python/issues/1046)) ([e64d084](https://github.com/googleapis/google-auth-library-python/commit/e64d0847276d456a95b171f5b79207e94ab818f3))

## [2.6.6](https://github.com/googleapis/google-auth-library-python/compare/v2.6.5...v2.6.6) (2022-04-21)


### Bug Fixes

* silence TypeError during tear down stage ([#1027](https://github.com/googleapis/google-auth-library-python/issues/1027)) ([952a6aa](https://github.com/googleapis/google-auth-library-python/commit/952a6aad888140c13815aada95f33792e414e061))

## [2.6.5](https://github.com/googleapis/google-auth-library-python/compare/v2.6.4...v2.6.5) (2022-04-14)


### Bug Fixes

* add additional missing import in _default.py ([#1018](https://github.com/googleapis/google-auth-library-python/issues/1018)) ([638331b](https://github.com/googleapis/google-auth-library-python/commit/638331b5b89c807b40c23c1e6333845d9b7e169a))

## [2.6.4](https://github.com/googleapis/google-auth-library-python/compare/v2.6.3...v2.6.4) (2022-04-12)


### Bug Fixes

* fix missing import in _default.py ([#1015](https://github.com/googleapis/google-auth-library-python/issues/1015)) ([63f4e38](https://github.com/googleapis/google-auth-library-python/commit/63f4e38153ded9fe9b51b83a1de74f3b71f73abc))

## [2.6.3](https://github.com/googleapis/google-auth-library-python/compare/v2.6.2...v2.6.3) (2022-04-06)


### Bug Fixes

* change requests lib import place ([#1010](https://github.com/googleapis/google-auth-library-python/issues/1010)) ([c753c08](https://github.com/googleapis/google-auth-library-python/commit/c753c08d2c78295173bb1160e8a74e819a352c33))
* clean up HTTP session and pool during tear down phase ([#1007](https://github.com/googleapis/google-auth-library-python/issues/1007)) ([d057376](https://github.com/googleapis/google-auth-library-python/commit/d057376245283402fe0b772ca138091c05864e5d))
* pin click version and update sys test creds ([#1008](https://github.com/googleapis/google-auth-library-python/issues/1008)) ([ae2804b](https://github.com/googleapis/google-auth-library-python/commit/ae2804bf292b5c8e6f935d2d0751db8fbe95a7b3))

## [2.6.2](https://github.com/googleapis/google-auth-library-python/compare/v2.6.1...v2.6.2) (2022-03-16)


### Bug Fixes

* Rename aws imdsv2 url field and update token lifetime ([#982](https://github.com/googleapis/google-auth-library-python/issues/982)) ([818e6d2](https://github.com/googleapis/google-auth-library-python/commit/818e6d2e63e58601499f0eaac1dd160345d9d6e4))


### Miscellaneous Chores

* let release-please finish the release ([#991](https://github.com/googleapis/google-auth-library-python/issues/991)) ([d2bdc9a](https://github.com/googleapis/google-auth-library-python/commit/d2bdc9a8a23930a01e5b8445e869a135511977cf))

## [2.6.1](https://github.com/googleapis/google-auth-library-python/compare/v2.6.0...v2.6.1) (2022-02-09)


### Bug Fixes

* Add AWS session token to metadata requests ([#958](https://github.com/googleapis/google-auth-library-python/issues/958)) ([5c7f734](https://github.com/googleapis/google-auth-library-python/commit/5c7f7342179d007e9e779ffe8734d540cdf36fde))

## [2.6.0](https://github.com/googleapis/google-auth-library-python/compare/v2.5.0...v2.6.0) (2022-01-31)


### Features

* ADC can load an impersonated service account credentials. ([#962](https://github.com/googleapis/google-auth-library-python/issues/962)) ([52c8ef9](https://github.com/googleapis/google-auth-library-python/commit/52c8ef90058120d7d04d3d201adc111664be526c))


### Bug Fixes

* revert "feat: add api key support ([#826](https://github.com/googleapis/google-auth-library-python/issues/826))" ([#964](https://github.com/googleapis/google-auth-library-python/issues/964)) ([f9f23f4](https://github.com/googleapis/google-auth-library-python/commit/f9f23f4370f2a7a5b2c66ee56a5e700ef03b5b06))

## [2.5.0](https://github.com/googleapis/google-auth-library-python/compare/v2.4.1...v2.5.0) (2022-01-25)


### Features

* ADC can load an impersonated service account credentials.  ([#956](https://github.com/googleapis/google-auth-library-python/issues/956)) ([a8eb4c8](https://github.com/googleapis/google-auth-library-python/commit/a8eb4c8693055a3420cfe9c3420aae2bc8cd465a))

## [2.4.1](https://github.com/googleapis/google-auth-library-python/compare/v2.4.0...v2.4.1) (2022-01-21)


### Bug Fixes

* urllib3 import ([#953](https://github.com/googleapis/google-auth-library-python/issues/953)) ([c8b5cae](https://github.com/googleapis/google-auth-library-python/commit/c8b5cae3da5eb9d40067d38dac51a4a8c1e0763e))

## [2.4.0](https://github.com/googleapis/google-auth-library-python/compare/v2.3.3...v2.4.0) (2022-01-20)


### Features

* add 'py.typed' declaration ([#919](https://github.com/googleapis/google-auth-library-python/issues/919)) ([c993504](https://github.com/googleapis/google-auth-library-python/commit/c99350455d0f7fd3aab950ac47b43000c73dd312))
* add api key support ([#826](https://github.com/googleapis/google-auth-library-python/issues/826)) ([3b15092](https://github.com/googleapis/google-auth-library-python/commit/3b15092b3461278400e4683060f64a96d50587c4))


### Bug Fixes

* **deps:** allow cachetools 5.0 for python 3.7+ ([#937](https://github.com/googleapis/google-auth-library-python/issues/937)) ([1eae37d](https://github.com/googleapis/google-auth-library-python/commit/1eae37db7f6fceb32d6ef0041962ce1755d2116c))
* fix the message format for metadata server exception ([#916](https://github.com/googleapis/google-auth-library-python/issues/916)) ([e756f08](https://github.com/googleapis/google-auth-library-python/commit/e756f08dc78616040ab8fbd7db20903137ccf0c7))


### Documentation

* fix intersphinx link for 'requests-oauthlib' ([#921](https://github.com/googleapis/google-auth-library-python/issues/921)) ([967be4f](https://github.com/googleapis/google-auth-library-python/commit/967be4f4e2a43ba7e240d7acb01b6b992d40e6ec))
* note ValueError in `verify_oauth2_token` ([#928](https://github.com/googleapis/google-auth-library-python/issues/928)) ([82bc5f0](https://github.com/googleapis/google-auth-library-python/commit/82bc5f08111de78a2b475b0310d3f35470680dbe))

## [2.3.3](https://www.github.com/googleapis/google-auth-library-python/compare/v2.3.2...v2.3.3) (2021-11-01)


### Bug Fixes

* add fetch_id_token_credentials ([#866](https://www.github.com/googleapis/google-auth-library-python/issues/866)) ([8f1e9cf](https://www.github.com/googleapis/google-auth-library-python/commit/8f1e9cfd56dbaae0dff64499e1d0cf55abc5b97e))
* fix error in sign_bytes ([#905](https://www.github.com/googleapis/google-auth-library-python/issues/905)) ([ef31284](https://www.github.com/googleapis/google-auth-library-python/commit/ef3128474431b07d1d519209ea61622bc245ce91))
* use 'int.to_bytes' and 'int.from_bytes' for py3 ([#904](https://www.github.com/googleapis/google-auth-library-python/issues/904)) ([bd0ccc5](https://www.github.com/googleapis/google-auth-library-python/commit/bd0ccc5fe77d55f7a19f5278d6b60587c393ee3c))

## [2.3.2](https://www.github.com/googleapis/google-auth-library-python/compare/v2.3.1...v2.3.2) (2021-10-26)


### Bug Fixes

* add clock_skew_in_seconds to verify_token functions ([#894](https://www.github.com/googleapis/google-auth-library-python/issues/894)) ([8e95c1e](https://www.github.com/googleapis/google-auth-library-python/commit/8e95c1e458793593972b6b05a355aaeaecd31670))

## [2.3.1](https://www.github.com/googleapis/google-auth-library-python/compare/v2.3.0...v2.3.1) (2021-10-21)


### Bug Fixes

* add back python 2.7 for gcloud usage only ([#892](https://www.github.com/googleapis/google-auth-library-python/issues/892)) ([5bd5ccf](https://www.github.com/googleapis/google-auth-library-python/commit/5bd5ccf7cf229f033c7152ce0b650a40feb25f81))


### Documentation

* Fix formatting of `GCE_METADATA_HOST` ([#890](https://www.github.com/googleapis/google-auth-library-python/issues/890)) ([e2b3c98](https://www.github.com/googleapis/google-auth-library-python/commit/e2b3c98cd8c67b702be1b711c06ee7b9bbedb8ba))

## [2.3.0](https://www.github.com/googleapis/google-auth-library-python/compare/v2.2.1...v2.3.0) (2021-10-07)


### Features

* add support for Python 3.10 ([#882](https://www.github.com/googleapis/google-auth-library-python/issues/882)) ([19d41f8](https://www.github.com/googleapis/google-auth-library-python/commit/19d41f8ec94ab0148d2f09a5d560ae237a87ffdb))


### Bug Fixes

* ADC with impersonated workforce pools ([#877](https://www.github.com/googleapis/google-auth-library-python/issues/877)) ([10bd9fb](https://www.github.com/googleapis/google-auth-library-python/commit/10bd9fbecd462435246afa46fd666a2836cd9e89))

## [2.2.1](https://www.github.com/googleapis/google-auth-library-python/compare/v2.2.0...v2.2.1) (2021-09-28)


### Bug Fixes

* disable self signed jwt for domain wide delegation ([#873](https://www.github.com/googleapis/google-auth-library-python/issues/873)) ([0cd15e2](https://www.github.com/googleapis/google-auth-library-python/commit/0cd15e2ae20f7caddf9eb2d069064058d3c14ad7))

## [2.2.0](https://www.github.com/googleapis/google-auth-library-python/compare/v2.1.0...v2.2.0) (2021-09-21)


### Features

* add support for workforce pool credentials ([#868](https://www.github.com/googleapis/google-auth-library-python/issues/868)) ([993bab2](https://www.github.com/googleapis/google-auth-library-python/commit/993bab2aaacf3034e09d9f0f25d36c0e815d3a29))

## [2.1.0](https://www.github.com/googleapis/google-auth-library-python/compare/v2.0.2...v2.1.0) (2021-09-10)


### Features

* Improve handling of clock skew ([#858](https://www.github.com/googleapis/google-auth-library-python/issues/858)) ([45c4491](https://www.github.com/googleapis/google-auth-library-python/commit/45c4491fb971c9edf590b27b9e271b7a23a1bba6))


### Bug Fixes

* add SAML challenge to reauth ([#819](https://www.github.com/googleapis/google-auth-library-python/issues/819)) ([13aed5f](https://www.github.com/googleapis/google-auth-library-python/commit/13aed5ffe3ba435004ab48202462452f04d7cb29))
* disable warning if quota project id provided to auth.default() ([#856](https://www.github.com/googleapis/google-auth-library-python/issues/856)) ([11ebaeb](https://www.github.com/googleapis/google-auth-library-python/commit/11ebaeb9d7c0862916154cfb810238574507629a))
* rename CLOCK_SKEW and separate client/server user case ([#863](https://www.github.com/googleapis/google-auth-library-python/issues/863)) ([738611b](https://www.github.com/googleapis/google-auth-library-python/commit/738611bd2914f0fd5fa8b49b65f56ef321829c85))

## [2.0.2](https://www.github.com/googleapis/google-auth-library-python/compare/v2.0.1...v2.0.2) (2021-08-25)


### Bug Fixes

* use 'int.to_bytes' rather than deprecated crypto wrapper ([#848](https://www.github.com/googleapis/google-auth-library-python/issues/848)) ([b79b554](https://www.github.com/googleapis/google-auth-library-python/commit/b79b55407b31933c9a8fe6de01478fa00a33fa2b))
* use int.from_bytes ([#846](https://www.github.com/googleapis/google-auth-library-python/issues/846)) ([466aed9](https://www.github.com/googleapis/google-auth-library-python/commit/466aed99f5c2ba15d2036fa21cc83b3f0fc22639))

## [2.0.1](https://www.github.com/googleapis/google-auth-library-python/compare/v2.0.0...v2.0.1) (2021-08-17)


### Bug Fixes

* normalize AWS paths correctly on windows ([#842](https://www.github.com/googleapis/google-auth-library-python/issues/842)) ([4e0fb1c](https://www.github.com/googleapis/google-auth-library-python/commit/4e0fb1cee78ee56b878b6e12be3b3c58df242b05))

## [2.0.0](https://www.github.com/googleapis/google-auth-library-python/compare/v2.0.0-b1...v2.0.0) (2021-08-16)


### ⚠ BREAKING CHANGES
* drop support for Python 2.7 ([#778](https://www.github.com/googleapis/google-auth-library-python/issues/778)) ([560cf1e](https://www.github.com/googleapis/google-auth-library-python/commit/560cf1ed02a900436c5d9e0a0fb3f94b5fd98c55))


### Features

* service account is able to use a private token endpoint ([#835](https://www.github.com/googleapis/google-auth-library-python/issues/835)) ([20b817a](https://www.github.com/googleapis/google-auth-library-python/commit/20b817af8e202b0331998e5abde4e2a5aab51f9a))


### Bug Fixes

* downscoping documentation bugs ([#830](https://www.github.com/googleapis/google-auth-library-python/issues/830)) ([da8bb13](https://www.github.com/googleapis/google-auth-library-python/commit/da8bb13c1349e771ffc2e125256030495c53d956))
* Fix missing space in error message. ([#821](https://www.github.com/googleapis/google-auth-library-python/issues/821)) ([7b03988](https://www.github.com/googleapis/google-auth-library-python/commit/7b039888aeb6ec7691d91c9afce182b17f02b1a6))


### Documentation

* update user guide/references for downscoped creds ([#827](https://www.github.com/googleapis/google-auth-library-python/issues/827)) ([d1840dc](https://www.github.com/googleapis/google-auth-library-python/commit/d1840dcdcd03dfd7fdfa81d08da68402f6f8b658))

## [2.0.0b1](https://www.github.com/googleapis/google-auth-library-python/compare/v1.34.0...v2.0.0b1) (2021-08-03)


### ⚠ BREAKING CHANGES

* drop support for Python 2.7 ([#778](https://www.github.com/googleapis/google-auth-library-python/issues/778)) ([560cf1e](https://www.github.com/googleapis/google-auth-library-python/commit/560cf1ed02a900436c5d9e0a0fb3f94b5fd98c55))

## [1.34.0](https://www.github.com/googleapis/google-auth-library-python/compare/v1.33.1...v1.34.0) (2021-07-23)


### Features

* support refresh callable on google.oauth2.credentials.Credentials ([#812](https://www.github.com/googleapis/google-auth-library-python/issues/812)) ([ec2fb18](https://www.github.com/googleapis/google-auth-library-python/commit/ec2fb18e7f0f452fb20e43fd0bfbb788bcf7f46b))


### Bug Fixes

* do not use the GAE APIs on gen2+ runtimes ([#807](https://www.github.com/googleapis/google-auth-library-python/issues/807)) ([7f7d92d](https://www.github.com/googleapis/google-auth-library-python/commit/7f7d92d63ffee91859fc819416af78cef3baf574))

## [1.33.1](https://www.github.com/googleapis/google-auth-library-python/compare/v1.33.0...v1.33.1) (2021-07-20)


### Bug Fixes

* fallback to source creds expiration in downscoped tokens ([#805](https://www.github.com/googleapis/google-auth-library-python/issues/805)) ([dfad661](https://www.github.com/googleapis/google-auth-library-python/commit/dfad66128c6ee7513e5565d39bc7b002055dd0d5))


### Reverts

* revert "feat: service account is able to use a private token endpoint ([#784](https://www.github.com/googleapis/google-auth-library-python/issues/784))" ([#808](https://www.github.com/googleapis/google-auth-library-python/issues/808)) ([d94e65c](https://www.github.com/googleapis/google-auth-library-python/commit/d94e65c0e441183403608d762b92b30b77e21eeb))

## [1.33.0](https://www.github.com/googleapis/google-auth-library-python/compare/v1.32.1...v1.33.0) (2021-07-14)


### Features

* define `CredentialAccessBoundary` classes ([#793](https://www.github.com/googleapis/google-auth-library-python/issues/793)) ([d883921](https://www.github.com/googleapis/google-auth-library-python/commit/d883921ae8fdc92b2c2cf1b3a5cd389e1287eb60))
* define `google.auth.downscoped.Credentials` class ([#801](https://www.github.com/googleapis/google-auth-library-python/issues/801)) ([2f5c3a6](https://www.github.com/googleapis/google-auth-library-python/commit/2f5c3a636192c20cf4c92c3831d1f485031d24d2))
* service account is able to use a private token endpoint ([#784](https://www.github.com/googleapis/google-auth-library-python/issues/784)) ([0e26409](https://www.github.com/googleapis/google-auth-library-python/commit/0e264092e35ac02ad68d5d91424ecba5397daa41))


### Bug Fixes

* fix fetch_id_token credential lookup order to match adc ([#748](https://www.github.com/googleapis/google-auth-library-python/issues/748)) ([c34452e](https://www.github.com/googleapis/google-auth-library-python/commit/c34452ef450c42cfef37a1b0c548bb422302dd5d))


### Documentation

* fix code block formatting in 'user-guide.rst' ([#794](https://www.github.com/googleapis/google-auth-library-python/issues/794)) ([4fd84bd](https://www.github.com/googleapis/google-auth-library-python/commit/4fd84bdf43694af5107dc8c8b443c06ba2f61d2c))

## [1.32.1](https://www.github.com/googleapis/google-auth-library-python/compare/v1.32.0...v1.32.1) (2021-06-30)


### Bug Fixes

* avoid leaking sub-session created for '_auth_request' ([#789](https://www.github.com/googleapis/google-auth-library-python/issues/789)) ([2079ab5](https://www.github.com/googleapis/google-auth-library-python/commit/2079ab5e1db464f502248ae4f9e424deeef87fb2))

## [1.32.0](https://www.github.com/googleapis/google-auth-library-python/compare/v1.31.0...v1.32.0) (2021-06-16)


### Features

* allow scopes for self signed jwt ([#776](https://www.github.com/googleapis/google-auth-library-python/issues/776)) ([2cfe655](https://www.github.com/googleapis/google-auth-library-python/commit/2cfe655bba837170abc07701557a1a5e0fe3294e))

## [1.31.0](https://www.github.com/googleapis/google-auth-library-python/compare/v1.30.2...v1.31.0) (2021-06-09)


### Features

* define useful properties on `google.auth.external_account.Credentials` ([#770](https://www.github.com/googleapis/google-auth-library-python/issues/770)) ([f97499c](https://www.github.com/googleapis/google-auth-library-python/commit/f97499c718af70d17c17e0c58d6381273eceabcd))


### Bug Fixes

* avoid deleting items while iterating ([#772](https://www.github.com/googleapis/google-auth-library-python/issues/772)) ([a5e6b65](https://www.github.com/googleapis/google-auth-library-python/commit/a5e6b651aa8ad407ce087fe32f40b46925bae527))

## [1.30.2](https://www.github.com/googleapis/google-auth-library-python/compare/v1.30.1...v1.30.2) (2021-06-03)


### Bug Fixes

* **dependencies:** add urllib3 and requests to aiohttp extra ([#755](https://www.github.com/googleapis/google-auth-library-python/issues/755)) ([a923442](https://www.github.com/googleapis/google-auth-library-python/commit/a9234423cb2b69068fc0d30a5a0ee86a599ab8b7))
* enforce constraints during unit tests ([#760](https://www.github.com/googleapis/google-auth-library-python/issues/760)) ([1a6496a](https://www.github.com/googleapis/google-auth-library-python/commit/1a6496abfc17ab781bfa485dc74d0f7dbbe0c44b)), closes [#759](https://www.github.com/googleapis/google-auth-library-python/issues/759)
* session object was never used in aiohttp request ([#700](https://www.github.com/googleapis/google-auth-library-python/issues/700)) ([#701](https://www.github.com/googleapis/google-auth-library-python/issues/701)) ([09e0389](https://www.github.com/googleapis/google-auth-library-python/commit/09e0389db72cc9d6c5dde34864cb54d717dc0b92))

## [1.30.1](https://www.github.com/googleapis/google-auth-library-python/compare/v1.30.0...v1.30.1) (2021-05-20)


### Bug Fixes

* allow user to customize context aware metadata path in _mtls_helper ([#754](https://www.github.com/googleapis/google-auth-library-python/issues/754)) ([e697687](https://www.github.com/googleapis/google-auth-library-python/commit/e6976879b392508c022610ab3ea2ea55c7089c63))
* fix function name in signing error message ([#751](https://www.github.com/googleapis/google-auth-library-python/issues/751)) ([e9ca25f](https://www.github.com/googleapis/google-auth-library-python/commit/e9ca25fa39a112cc1a376388ab47a4e1b3ea746c))

## [1.30.0](https://www.github.com/googleapis/google-auth-library-python/compare/v1.29.0...v1.30.0) (2021-04-23)


### Features

* add reauth support to async user credentials for gcloud ([#738](https://www.github.com/googleapis/google-auth-library-python/issues/738)) ([9e10823](https://www.github.com/googleapis/google-auth-library-python/commit/9e1082366d113286bc063051fd76b4799791d943)). This internal feature is for gcloud developers only. 

## [1.29.0](https://www.github.com/googleapis/google-auth-library-python/compare/v1.28.1...v1.29.0) (2021-04-15)


### Features

* add reauth feature to user credentials for gcloud ([#727](https://www.github.com/googleapis/google-auth-library-python/issues/727)) ([82293fe](https://www.github.com/googleapis/google-auth-library-python/commit/82293fe2caaf5258babb5df1cff0a5ddc9e44b38)). This internal feature is for gcloud developers only.


### Bug Fixes

* Allow multiple audiences for id_token.verify_token ([#733](https://www.github.com/googleapis/google-auth-library-python/issues/733)) ([56c3946](https://www.github.com/googleapis/google-auth-library-python/commit/56c394680ac6dfc07c611a9eb1e030e32edd4fe1))

## [1.28.1](https://www.github.com/googleapis/google-auth-library-python/compare/v1.28.0...v1.28.1) (2021-04-08)


### Bug Fixes

* support custom alg in jwt header for signing ([#729](https://www.github.com/googleapis/google-auth-library-python/issues/729)) ([0a83706](https://www.github.com/googleapis/google-auth-library-python/commit/0a83706c9d65f7d5a30ea3b42c5beac269ed2a25))

## [1.28.0](https://www.github.com/googleapis/google-auth-library-python/compare/v1.27.1...v1.28.0) (2021-03-16)


### Features

* allow the AWS_DEFAULT_REGION environment variable ([#721](https://www.github.com/googleapis/google-auth-library-python/issues/721)) ([199da47](https://www.github.com/googleapis/google-auth-library-python/commit/199da4781029916dc075738ec7bd173bd89abe54))
* expose library version at `google.auth.__version` ([#683](https://www.github.com/googleapis/google-auth-library-python/issues/683)) ([a2cbc32](https://www.github.com/googleapis/google-auth-library-python/commit/a2cbc3245460e1ae1d310de6a2a4007d5a3a06b7))


### Bug Fixes

* fix unit tests so they can work in g3 ([#714](https://www.github.com/googleapis/google-auth-library-python/issues/714)) ([d80c85f](https://www.github.com/googleapis/google-auth-library-python/commit/d80c85f285ae1a44ddc5a5d94a66e065a79f6d19))

## [1.27.1](https://www.github.com/googleapis/google-auth-library-python/compare/v1.27.0...v1.27.1) (2021-02-26)


### Bug Fixes

* ignore gcloud warning when getting project id ([#708](https://www.github.com/googleapis/google-auth-library-python/issues/708)) ([3f2f3ea](https://www.github.com/googleapis/google-auth-library-python/commit/3f2f3eaf09006d3d0ec9c030d359114238479279))
* use gcloud creds flow ([#705](https://www.github.com/googleapis/google-auth-library-python/issues/705)) ([333cb76](https://www.github.com/googleapis/google-auth-library-python/commit/333cb765b52028329ec3ca04edf32c5764b1db68))

## [1.27.0](https://www.github.com/googleapis/google-auth-library-python/compare/v1.26.1...v1.27.0) (2021-02-16)


### Features

* workload identity federation support ([#698](https://www.github.com/googleapis/google-auth-library-python/issues/698)) ([d4d7f38](https://www.github.com/googleapis/google-auth-library-python/commit/d4d7f3815e0cea3c9f39a5204a4f001de99568e9))


### Bug Fixes

* add pyopenssl as extra dependency ([#697](https://www.github.com/googleapis/google-auth-library-python/issues/697)) ([aeab5d0](https://www.github.com/googleapis/google-auth-library-python/commit/aeab5d07c5538f3d8cce817df24199534572b97d))

## [1.26.1](https://www.github.com/googleapis/google-auth-library-python/compare/v1.26.0...v1.26.1) (2021-02-11)


### Documentation

* fix a typo in the user guide (avaiable -> available) ([#680](https://www.github.com/googleapis/google-auth-library-python/issues/680)) ([684457a](https://www.github.com/googleapis/google-auth-library-python/commit/684457afd3f81892e12d983a61672d7ea9bbe296))

### Bug Fixes

* revert workload identity federation support ([#691](https://github.com/googleapis/google-auth-library-python/pull/691))

## [1.26.0](https://www.github.com/googleapis/google-auth-library-python/compare/v1.25.0...v1.26.0) (2021-02-09)


### Features

* workload identity federation support ([#686](https://www.github.com/googleapis/google-auth-library-python/issues/686)) ([5dcd2b1](https://www.github.com/googleapis/google-auth-library-python/commit/5dcd2b1bdd9d21522636d959cffc49ee29dda88f))

## [1.25.0](https://www.github.com/googleapis/google-auth-library-python/compare/v1.24.0...v1.25.0) (2021-02-03)


### Features

* support self-signed jwt in requests and urllib3 transports ([#679](https://www.github.com/googleapis/google-auth-library-python/issues/679)) ([7a94acb](https://www.github.com/googleapis/google-auth-library-python/commit/7a94acb50e75fe0a51688e0f968bca3fa9bd9082))
* use self-signed jwt for service account ([#665](https://www.github.com/googleapis/google-auth-library-python/issues/665)) ([bf5ce0c](https://www.github.com/googleapis/google-auth-library-python/commit/bf5ce0c56c10f655ced6630653f0f2ad47fcceeb))

## [1.24.0](https://www.github.com/googleapis/google-auth-library-python/compare/v1.23.0...v1.24.0) (2020-12-11)


### Features

* add Python 3.9 support, drop Python 3.5 support ([#655](https://www.github.com/googleapis/google-auth-library-python/issues/655)) ([6de753d](https://www.github.com/googleapis/google-auth-library-python/commit/6de753d585254c813b3e6cbde27bf5466261ba10)), closes [#654](https://www.github.com/googleapis/google-auth-library-python/issues/654)


### Bug Fixes

* avoid losing the original '_include_email' parameter in impersonated credentials ([#626](https://www.github.com/googleapis/google-auth-library-python/issues/626)) ([fd9b5b1](https://www.github.com/googleapis/google-auth-library-python/commit/fd9b5b10c80950784bd37ee56e32c505acb5078d))


### Documentation

* fix typo in import ([#651](https://www.github.com/googleapis/google-auth-library-python/issues/651)) ([3319ea8](https://www.github.com/googleapis/google-auth-library-python/commit/3319ea8ae876c73a94f51237b3bbb3f5df2aef89)), closes [#650](https://www.github.com/googleapis/google-auth-library-python/issues/650)

## [1.23.0](https://www.github.com/googleapis/google-auth-library-python/compare/v1.22.1...v1.23.0) (2020-10-29)


### Features

* Add custom scopes for access tokens from the metadata service ([#633](https://www.github.com/googleapis/google-auth-library-python/issues/633)) ([0323cf3](https://www.github.com/googleapis/google-auth-library-python/commit/0323cf390b16e8483660ac88775e8ea4e7f7702d))


### Bug Fixes

* **deps:** Revert "fix: pin 'aoihttp < 3.7.0dev' ([#634](https://www.github.com/googleapis/google-auth-library-python/issues/634))" ([#632](https://www.github.com/googleapis/google-auth-library-python/issues/632)) ([#640](https://www.github.com/googleapis/google-auth-library-python/issues/640)) ([b790e65](https://www.github.com/googleapis/google-auth-library-python/commit/b790e6535cc37591b23866027a426cde312e07c1))
* pin 'aoihttp < 3.7.0dev' ([#634](https://www.github.com/googleapis/google-auth-library-python/issues/634)) ([05f9524](https://www.github.com/googleapis/google-auth-library-python/commit/05f95246fab928fe2f445781117eeac8088497fb))
* remove checks for ancient versions of Cryptography ([#596](https://www.github.com/googleapis/google-auth-library-python/issues/596)) ([6407258](https://www.github.com/googleapis/google-auth-library-python/commit/6407258956ec42e3b722418cb7f366e5ae9272ec)), closes [/github.com/googleapis/google-auth-library-python/issues/595#issuecomment-683903062](https://www.github.com/googleapis//github.com/googleapis/google-auth-library-python/issues/595/issues/issuecomment-683903062)

## [1.22.1](https://www.github.com/googleapis/google-auth-library-python/compare/v1.22.0...v1.22.1) (2020-10-05)


### Bug Fixes

* move aiohttp to extra as it is currently internal surface ([#619](https://www.github.com/googleapis/google-auth-library-python/issues/619)) ([a924011](https://www.github.com/googleapis/google-auth-library-python/commit/a9240111e7af29338624d98ee10aed31462f4d19)), closes [#618](https://www.github.com/googleapis/google-auth-library-python/issues/618)

## [1.22.0](https://www.github.com/googleapis/google-auth-library-python/compare/v1.21.3...v1.22.0) (2020-09-28)


### Features

* add asyncio based auth flow ([#612](https://www.github.com/googleapis/google-auth-library-python/issues/612)) ([7e15258](https://www.github.com/googleapis/google-auth-library-python/commit/7e1525822d51bd9ce7dffca42d71313e6e776fcd)), closes [#572](https://www.github.com/googleapis/google-auth-library-python/issues/572)

## [1.21.3](https://www.github.com/googleapis/google-auth-library-python/compare/v1.21.2...v1.21.3) (2020-09-22)


### Bug Fixes

* fix expiry for `to_json()` ([#589](https://www.github.com/googleapis/google-auth-library-python/issues/589)) ([d0e0aba](https://www.github.com/googleapis/google-auth-library-python/commit/d0e0aba0a9f665268ffa1b22d44f4bd7e9b449d6)), closes [/github.com/googleapis/oauth2client/blob/master/oauth2client/client.py#L55](https://www.github.com/googleapis//github.com/googleapis/oauth2client/blob/master/oauth2client/client.py/issues/L55)

## [1.21.2](https://www.github.com/googleapis/google-auth-library-python/compare/v1.21.1...v1.21.2) (2020-09-08)


### Bug Fixes

* migrate signBlob to iamcredentials.googleapis.com ([#600](https://www.github.com/googleapis/google-auth-library-python/issues/600)) ([694d83f](https://www.github.com/googleapis/google-auth-library-python/commit/694d83fd23c0e8c2fde27136d1b3f8f6db6338a6))

## [1.21.1](https://www.github.com/googleapis/google-auth-library-python/compare/v1.21.0...v1.21.1) (2020-09-03)


### Bug Fixes

* dummy commit to trigger a auto release ([#597](https://www.github.com/googleapis/google-auth-library-python/issues/597)) ([d32f7df](https://www.github.com/googleapis/google-auth-library-python/commit/d32f7df4895122ef23b664672d7db3f58d9b7d36))

## [1.21.0](https://www.github.com/googleapis/google-auth-library-python/compare/v1.20.1...v1.21.0) (2020-08-27)


### Features

* add GOOGLE_API_USE_CLIENT_CERTIFICATE support ([#592](https://www.github.com/googleapis/google-auth-library-python/issues/592)) ([c0c995f](https://www.github.com/googleapis/google-auth-library-python/commit/c0c995f3de237a2346b59797ee7c4d44ff2a197c))

## [1.20.1](https://www.github.com/googleapis/google-auth-library-python/compare/v1.20.0...v1.20.1) (2020-08-06)


### Bug Fixes

* reduce refresh clock skew to 10 seconds ([#581](https://www.github.com/googleapis/google-auth-library-python/issues/581)) ([42321ba](https://www.github.com/googleapis/google-auth-library-python/commit/42321bafd38a8bd806f4d01bfa0eda3b5a961667))
* set Content-Type header in the request to signBlob API to avoid Invalid JSON payload error ([#439](https://www.github.com/googleapis/google-auth-library-python/issues/439)) ([20f82e2](https://www.github.com/googleapis/google-auth-library-python/commit/20f82e22b7e8c6c7fdd29e08eaf7b4cf2abdcf37))

## [1.20.0](https://www.github.com/googleapis/google-auth-library-python/compare/v1.19.2...v1.20.0) (2020-07-23)


### Features

* Add debug logging that can help with diagnosing auth lib. path ([#473](https://www.github.com/googleapis/google-auth-library-python/issues/473)) ([ecd88d4](https://www.github.com/googleapis/google-auth-library-python/commit/ecd88d4f0efc5c619ebd3e3fa7e2472f11c63452))
* Show the transport exception that happened for GCE Metadata ([#474](https://www.github.com/googleapis/google-auth-library-python/issues/474)) ([23919bb](https://www.github.com/googleapis/google-auth-library-python/commit/23919bb60e5f9d9b73644e9a2e127d4d1dd68e8c))
* **packaging:** add support for Python 3.8 ([#569](https://www.github.com/googleapis/google-auth-library-python/issues/569)) ([1aad54a](https://www.github.com/googleapis/google-auth-library-python/commit/1aad54af6b1d5da73d7471cdbfaf0d0b37c5fde6)), closes [#568](https://www.github.com/googleapis/google-auth-library-python/issues/568)

## [1.19.2](https://www.github.com/googleapis/google-auth-library-python/compare/v1.19.1...v1.19.2) (2020-07-17)


### Bug fixes
 
* Revert "fix: migrate signBlob to iamcredentials.googleapis.com"  ([#563](https://www.github.com/googleapis/google-auth-library-python/issues/563)) ([a48b5b](https://www.github.com/googleapis/google-auth-library-python/commit/a48b5b9135b30ff06f1fe18dd9dbe92ffcf3a272))

## [1.19.1](https://www.github.com/googleapis/google-auth-library-python/compare/v1.19.0...v1.19.1) (2020-07-15)


### Bug Fixes

* don't add empty quota project  ([#560](https://www.github.com/googleapis/google-auth-library-python/issues/560)) ([ab2be5d](https://www.github.com/googleapis/google-auth-library-python/commit/ab2be5de829e830979514683582c11f98fa943c7))

## [1.19.0](https://www.github.com/googleapis/google-auth-library-python/compare/v1.18.0...v1.19.0) (2020-07-09)


### Features

* add quota project to base credentials class ([#546](https://www.github.com/googleapis/google-auth-library-python/issues/546)) ([3dda7b2](https://www.github.com/googleapis/google-auth-library-python/commit/3dda7b2ab88aba7941b8b5281b4acbc7db74169b))
* check 'iss' in `verify_oauth2_token` ([#500](https://www.github.com/googleapis/google-auth-library-python/issues/500)) ([c05b8b5](https://www.github.com/googleapis/google-auth-library-python/commit/c05b8b52e3bbc096cf32e2d4bb5bd45986d3cd04))


### Bug Fixes

* migrate signBlob to iamcredentials.googleapis.com ([#553](https://www.github.com/googleapis/google-auth-library-python/issues/553)) ([038ae1b](https://www.github.com/googleapis/google-auth-library-python/commit/038ae1b78dc83e44ad39ef7ba15c607f62232087))


### Documentation

* remove 3.4 from supported versions list ([#549](https://www.github.com/googleapis/google-auth-library-python/issues/549)) ([8c84d0f](https://www.github.com/googleapis/google-auth-library-python/commit/8c84d0fb36d9eba6b319964ca0a22501efca805b))

## [1.18.0](https://www.github.com/googleapis/google-auth-library-python/compare/v1.17.2...v1.18.0) (2020-06-18)


### Features

* make ``load_credentials_from_file`` a public method ([#530](https://www.github.com/googleapis/google-auth-library-python/issues/530)) ([15d5fa9](https://www.github.com/googleapis/google-auth-library-python/commit/15d5fa946177581b52a5a9eb3ca285c088f5c45d))


### Bug Fixes

* no warning if quota_project_id is given ([#537](https://www.github.com/googleapis/google-auth-library-python/issues/537)) ([f30b45a](https://www.github.com/googleapis/google-auth-library-python/commit/f30b45a9b2f824c494724548732c5ce838218c30))

## [1.17.2](https://www.github.com/googleapis/google-auth-library-python/compare/v1.17.1...v1.17.2) (2020-06-12)


### Bug Fixes

* **dependencies:** Further restrict RSA versions ([#532](https://www.github.com/googleapis/google-auth-library-python/issues/532)) ([46677a0](https://www.github.com/googleapis/google-auth-library-python/commit/46677a0cb3bde6622be10061bc61daaff7a0aaca)), closes [#528](https://www.github.com/googleapis/google-auth-library-python/issues/528)

## [1.17.1](https://www.github.com/googleapis/google-auth-library-python/compare/v1.17.0...v1.17.1) (2020-06-11)


### Bug Fixes

* narrow acceptable RSA versions to maintain Python 2 compatability ([#528](https://www.github.com/googleapis/google-auth-library-python/issues/528)) ([9434868](https://www.github.com/googleapis/google-auth-library-python/commit/9434868a6789464549af1d4562f62d8a899b6809))

## [1.17.0](https://www.github.com/googleapis/google-auth-library-python/compare/v1.16.1...v1.17.0) (2020-06-10)


### Features

* add quota_project_id to service accounts; add with_quota_project methods ([#519](https://www.github.com/googleapis/google-auth-library-python/issues/519)) ([b12488c](https://www.github.com/googleapis/google-auth-library-python/commit/b12488cf552888299425c8009ea075511627cf08))

## [1.16.1](https://www.github.com/googleapis/google-auth-library-python/compare/v1.16.0...v1.16.1) (2020-06-04)


### Bug Fixes

* fix impersonated cred exception doc ([#521](https://www.github.com/googleapis/google-auth-library-python/issues/521)) ([9d5a9a9](https://www.github.com/googleapis/google-auth-library-python/commit/9d5a9a9884fecbd698a602d2a9fd9bec6b987de7))
* replace environment variable GCE_METADATA_ROOT with GCE_METADATA_HOST ([#433](https://www.github.com/googleapis/google-auth-library-python/issues/433)) ([8ffb4d3](https://www.github.com/googleapis/google-auth-library-python/commit/8ffb4d3e832607869026444e5a071c5f3e225fd2)), closes [#339](https://www.github.com/googleapis/google-auth-library-python/issues/339)

## [1.16.0](https://www.github.com/googleapis/google-auth-library-python/compare/v1.15.0...v1.16.0) (2020-05-28)


### Features

* add helper func to for default encrypted cert ([#514](https://www.github.com/googleapis/google-auth-library-python/issues/514)) ([f282aa4](https://www.github.com/googleapis/google-auth-library-python/commit/f282aa4acc73d5b56aa7d4bb745d286c3cf1fc39))


### Bug Fixes

* fix impersonated cred for gcloud ([#516](https://www.github.com/googleapis/google-auth-library-python/issues/516)) ([eb7be3f](https://www.github.com/googleapis/google-auth-library-python/commit/eb7be3fa98ace42b3e949a8af90bbb978ae7e455))

## [1.15.0](https://www.github.com/googleapis/google-auth-library-python/compare/v1.14.3...v1.15.0) (2020-05-15)


### Features

* encrypted mtls private key support ([#496](https://www.github.com/googleapis/google-auth-library-python/issues/496)) ([9dc9e9f](https://www.github.com/googleapis/google-auth-library-python/commit/9dc9e9f4ca65780b4d7f24e2c36021d2300b4006))


### Bug Fixes

* signBytes for impersonated credentials ([#506](https://www.github.com/googleapis/google-auth-library-python/issues/506)) ([ca8d98a](https://www.github.com/googleapis/google-auth-library-python/commit/ca8d98ab2e5277e53ab8df78beb1e75cdf5321e3)), closes [#338](https://www.github.com/googleapis/google-auth-library-python/issues/338)

## [1.14.3](https://www.github.com/googleapis/google-auth-library-python/compare/v1.14.2...v1.14.3) (2020-05-11)


### Bug Fixes

* catch exceptions.RefreshError ([#508](https://www.github.com/googleapis/google-auth-library-python/issues/508)) ([3d672e9](https://www.github.com/googleapis/google-auth-library-python/commit/3d672e9cddd9e8c4946290ab9f90ca9009b8be69))

## [1.14.2](https://www.github.com/googleapis/google-auth-library-python/compare/v1.14.1...v1.14.2) (2020-05-07)


### Bug Fixes

* support string type response.data ([#504](https://www.github.com/googleapis/google-auth-library-python/issues/504)) ([9b7228e](https://www.github.com/googleapis/google-auth-library-python/commit/9b7228ec849e311bcb4007ad3e23cf2f1e54a721))

## [1.14.1](https://www.github.com/googleapis/google-auth-library-python/compare/v1.14.0...v1.14.1) (2020-04-21)


### Bug Fixes

* support es256 raw format signature ([#490](https://www.github.com/googleapis/google-auth-library-python/issues/490)) ([cf2c0a9](https://www.github.com/googleapis/google-auth-library-python/commit/cf2c0a90701ce42f47df71281ae9cdf212c28e0e))

## [1.14.0](https://www.github.com/googleapis/google-auth-library-python/compare/v1.13.1...v1.14.0) (2020-04-13)


### Features

* add default client cert source util ([#486](https://www.github.com/googleapis/google-auth-library-python/issues/486)) ([ed41b49](https://www.github.com/googleapis/google-auth-library-python/commit/ed41b49e9d7ba7402b27107b7aa47eed06ac6c55))

## [1.13.1](https://www.github.com/googleapis/google-auth-library-python/compare/v1.13.0...v1.13.1) (2020-04-01)


### Bug Fixes

* invalid expiry type ([#481](https://www.github.com/googleapis/google-auth-library-python/issues/481)) ([7ae9a28](https://www.github.com/googleapis/google-auth-library-python/commit/7ae9a284dae16d274bfd4d876414f08efd6c3bff))

## [1.13.0](https://www.github.com/googleapis/google-auth-library-python/compare/v1.12.0...v1.13.0) (2020-04-01)


### Features

* add access token credentials ([#476](https://www.github.com/googleapis/google-auth-library-python/issues/476)) ([772dac6](https://www.github.com/googleapis/google-auth-library-python/commit/772dac6a6512230d32cb0dfae65a1a6aa9015049))
* add fetch_id_token to support id_token adc ([#469](https://www.github.com/googleapis/google-auth-library-python/issues/469)) ([506c565](https://www.github.com/googleapis/google-auth-library-python/commit/506c565a8c3c23a78fd0f17991bc6deb6f2528a9))
* consolidate mTLS channel errors ([#480](https://www.github.com/googleapis/google-auth-library-python/issues/480)) ([e83d446](https://www.github.com/googleapis/google-auth-library-python/commit/e83d4462f5c50f8424d9e54be32c29390115a9ed))
* Implement ES256 for JWT verification ([#340](https://www.github.com/googleapis/google-auth-library-python/issues/340)) ([e290a3d](https://www.github.com/googleapis/google-auth-library-python/commit/e290a3dbecc4767dd25ee14574951cdb6c2157cb))

## [1.12.0](https://www.github.com/googleapis/google-auth-library-python/compare/v1.11.3...v1.12.0) (2020-03-25)


### Features

* add mTLS ADC support for HTTP ([#457](https://www.github.com/googleapis/google-auth-library-python/issues/457)) ([bb9215a](https://www.github.com/googleapis/google-auth-library-python/commit/bb9215ad6dee6c1dc7f255a2e4ed7011b85bd6cf))
* add SslCredentials class for mTLS ADC ([#448](https://www.github.com/googleapis/google-auth-library-python/issues/448)) ([dafb41f](https://www.github.com/googleapis/google-auth-library-python/commit/dafb41fae3f513ea9a4f93404f6148bee7dda202))
* fetch id token from GCE metadata server ([#462](https://www.github.com/googleapis/google-auth-library-python/issues/462)) ([97e7700](https://www.github.com/googleapis/google-auth-library-python/commit/97e7700da031bfd80b63b1a3d2abc29c500936ef))


### Bug Fixes

* don't use threads for gRPC AuthMetadataPlugin ([#467](https://www.github.com/googleapis/google-auth-library-python/issues/467)) ([ee373f8](https://www.github.com/googleapis/google-auth-library-python/commit/ee373f88b512a38e791a1c085452c6c6da501eb6))
* make ThreadPoolExecutor a class var ([#461](https://www.github.com/googleapis/google-auth-library-python/issues/461)) ([b526473](https://www.github.com/googleapis/google-auth-library-python/commit/b5264730603947295cc97ecff2f6aef84aa3d6e9))

## [1.11.3](https://www.github.com/googleapis/google-auth-library-python/compare/v1.11.2...v1.11.3) (2020-03-13)


### Bug Fixes

* fix the scopes so test can pass for a local run ([#450](https://www.github.com/googleapis/google-auth-library-python/issues/450)) ([b2dd77f](https://www.github.com/googleapis/google-auth-library-python/commit/b2dd77fe4a538e1d165fc9d859c9a299f6832cda))
* only add IAM scope to credentials that can change scopes ([#451](https://www.github.com/googleapis/google-auth-library-python/issues/451)) ([82e224b](https://www.github.com/googleapis/google-auth-library-python/commit/82e224b0854950a5607cd028edbcbcdc3e9e6505))

## [1.11.2](https://www.github.com/googleapis/google-auth-library-python/compare/v1.11.1...v1.11.2) (2020-02-14)


### Reverts

* Revert "fix: update `_GOOGLE_OAUTH2_CERTS_URL` (#365)" (#444) ([901c259](https://www.github.com/googleapis/google-auth-library-python/commit/901c259b1764f5a305a542cbae14d926ba7a57db)), closes [#365](https://www.github.com/googleapis/google-auth-library-python/issues/365) [#444](https://www.github.com/googleapis/google-auth-library-python/issues/444)

## [1.11.1](https://www.github.com/googleapis/google-auth-library-python/compare/v1.11.0...v1.11.1) (2020-02-13)


### Bug Fixes

* compute engine id token credentials "with_target_audience" method ([#438](https://www.github.com/googleapis/google-auth-library-python/issues/438)) ([bc0ec93](https://www.github.com/googleapis/google-auth-library-python/commit/bc0ec93dc66fdcaa6a82222386623fa44f24ddfe))
* update `_GOOGLE_OAUTH2_CERTS_URL` ([#365](https://www.github.com/googleapis/google-auth-library-python/issues/365)) ([054db75](https://www.github.com/googleapis/google-auth-library-python/commit/054db75734756b0e82e7984ca07fa80025edc908))

## [1.11.0](https://www.github.com/googleapis/google-auth-library-python/compare/v1.10.2...v1.11.0) (2020-01-23)


### Features

* add non-None default timeout to AuthorizedSession.request() ([#435](https://www.github.com/googleapis/google-auth-library-python/issues/435)) ([d274a3a](https://www.github.com/googleapis/google-auth-library-python/commit/d274a3a2b3f913bc2cab4ca51f9c7fdef94b8f31)), closes [#434](https://www.github.com/googleapis/google-auth-library-python/issues/434) [googleapis/google-cloud-python#10182](https://www.github.com/googleapis/google-cloud-python/issues/10182)
* distinguish transport and execution time timeouts ([#424](https://www.github.com/googleapis/google-auth-library-python/issues/424)) ([52a733d](https://www.github.com/googleapis/google-auth-library-python/commit/52a733d604528fa86d05321bb74241a43aea4211)), closes [#423](https://github.com/googleapis/google-auth-library-python/issues/423)

## [1.10.2](https://www.github.com/googleapis/google-auth-library-python/compare/v1.10.1...v1.10.2) (2020-01-18)


### Bug Fixes

* make collections import compatible across Python versions ([#419](https://www.github.com/googleapis/google-auth-library-python/issues/419)) ([c5a3395](https://www.github.com/googleapis/google-auth-library-python/commit/c5a3395b8781e14c4566cf0e476b234d6a1c1224)), closes [#418](https://www.github.com/googleapis/google-auth-library-python/issues/418)

## [1.10.1](https://www.github.com/googleapis/google-auth-library-python/compare/v1.10.0...v1.10.1) (2020-01-10)


### Bug Fixes

* **google.auth.compute_engine.metadata:** add retry to google.auth.compute_engine._metadata.get() ([#398](https://www.github.com/googleapis/google-auth-library-python/issues/398)) ([af29c1a](https://www.github.com/googleapis/google-auth-library-python/commit/af29c1a9fd9282b38867961e4053f74f018a3815)), closes [#211](https://www.github.com/googleapis/google-auth-library-python/issues/211) [#323](https://www.github.com/googleapis/google-auth-library-python/issues/323) [#323](https://www.github.com/googleapis/google-auth-library-python/issues/323) [#211](https://www.github.com/googleapis/google-auth-library-python/issues/211)
* always pass body of type bytes to `google.auth.transport.Request` ([#421](https://www.github.com/googleapis/google-auth-library-python/issues/421)) ([a57a770](https://www.github.com/googleapis/google-auth-library-python/commit/a57a7708cfea635b5030f8c7ba10c967715f9a87)), closes [#318](https://www.github.com/googleapis/google-auth-library-python/issues/318)

## [1.10.0](https://www.github.com/googleapis/google-auth-library-python/compare/v1.9.0...v1.10.0) (2019-12-18)


### Features

* send quota project id in x-goog-user-project for OAuth2 credentials ([#412](https://www.github.com/googleapis/google-auth-library-python/issues/412)) ([32d71a5](https://www.github.com/googleapis/google-auth-library-python/commit/32d71a5858435af0818a705b754404882bb7bb9e)), closes [#400](https://www.github.com/googleapis/google-auth-library-python/issues/400)

## [1.9.0](https://www.github.com/googleapis/google-auth-library-python/compare/v1.8.2...v1.9.0) (2019-12-12)


### Features

* add timeout parameter to `AuthorizedSession.request()` ([#406](https://www.github.com/googleapis/google-auth-library-python/issues/406)) ([d86d7b8](https://www.github.com/googleapis/google-auth-library-python/commit/d86d7b8c43df152765c7fc59a54015361b46dcde))

## [1.8.2](https://www.github.com/googleapis/google-auth-library-python/compare/v1.8.1...v1.8.2) (2019-12-11)


### Bug Fixes

* revert "feat: send quota project id in x-goog-user-project header for OAuth2 credentials ([#400](https://www.github.com/googleapis/google-auth-library-python/issues/400))" ([#407](https://www.github.com/googleapis/google-auth-library-python/issues/407)) ([25ea942](https://www.github.com/googleapis/google-auth-library-python/commit/25ea942cef4378ff22adf235dd1baf1ca0d595f8))

## [1.8.1](https://www.github.com/googleapis/google-auth-library-python/compare/v1.8.0...v1.8.1) (2019-12-09)


### Bug Fixes

* revert "feat: add timeout to AuthorizedSession.request() ([#397](https://www.github.com/googleapis/google-auth-library-python/issues/397))" ([#401](https://www.github.com/googleapis/google-auth-library-python/issues/401)) ([451ecbd](https://www.github.com/googleapis/google-auth-library-python/commit/451ecbd48a910348bbf7a7b38162a044fad6e6e1))

## [1.8.0](https://www.github.com/googleapis/google-auth-library-python/compare/v1.7.2...v1.8.0) (2019-12-09)


### Features

* add `to_json` method to google.oauth2.credentials.Credentials ([#367](https://www.github.com/googleapis/google-auth-library-python/issues/367)) ([bfb1f8c](https://www.github.com/googleapis/google-auth-library-python/commit/bfb1f8cc8a706ce5ca2a14886c920ca2220ec349))
* add timeout to AuthorizedSession.request() ([#397](https://www.github.com/googleapis/google-auth-library-python/issues/397)) ([381dd40](https://www.github.com/googleapis/google-auth-library-python/commit/381dd400911d29926ffbf04e0f2ba53ef7bb997e))
* send quota project id in x-goog-user-project header for OAuth2 credentials ([#400](https://www.github.com/googleapis/google-auth-library-python/issues/400)) ([ab3dc1e](https://www.github.com/googleapis/google-auth-library-python/commit/ab3dc1e26f5240ea3456de364c7c5cb8f40f9583))

## [1.7.2](https://www.github.com/googleapis/google-auth-library-python/compare/v1.7.1...v1.7.2) (2019-12-02)


### Bug Fixes

* in token endpoint request, do not decode the response data if it is not encoded ([#393](https://www.github.com/googleapis/google-auth-library-python/issues/393)) ([3b5d3e2](https://www.github.com/googleapis/google-auth-library-python/commit/3b5d3e2192ce0cdc97854a1d70d5e382e454275c))
* make gRPC auth plugin non-blocking + add default timeout value for requests transport ([#390](https://www.github.com/googleapis/google-auth-library-python/issues/390)) ([0c33e9c](https://www.github.com/googleapis/google-auth-library-python/commit/0c33e9c0fe4f87fa46c8f1a5afe725a467ac5fcc)), closes [#351](https://www.github.com/googleapis/google-auth-library-python/issues/351)

## [1.7.1](https://www.github.com/googleapis/google-auth-library-python/compare/v1.7.0...v1.7.1) (2019-11-13)


### Bug Fixes

* change 'internal_failure' condition to also use `error' field ([#387](https://www.github.com/googleapis/google-auth-library-python/issues/387)) ([46bb58e](https://www.github.com/googleapis/google-auth-library-python/commit/46bb58e694716908a5ed00f05dbb794cdec667dd))

## 1.7.0

10-30-2019 17:11 PDT


### Implementation Changes
- Add retry loop  for fetching authentication token if any 'Internal Failure' occurs ([#368](https://github.com/googleapis/google-auth-library-python/pull/368))
- Use cls parameter instead of class ([#341](https://github.com/googleapis/google-auth-library-python/pull/341))

### New Features
- Add support for `impersonated_credentials.Sign`, `IDToken` ([#348](https://github.com/googleapis/google-auth-library-python/pull/348))
- Add downscoping to OAuth2 credentials ([#309](https://github.com/googleapis/google-auth-library-python/pull/309))

### Dependencies
- Update dependency cachetools to v3 ([#357](https://github.com/googleapis/google-auth-library-python/pull/357))
- Update dependency rsa to v4 ([#358](https://github.com/googleapis/google-auth-library-python/pull/358))
- Set an upper bound on dependencies version ([#352](https://github.com/googleapis/google-auth-library-python/pull/352))
- Require a minimum version of setuptools ([#322](https://github.com/googleapis/google-auth-library-python/pull/322))

### Documentation
- Add busunkim96 as maintainer ([#373](https://github.com/googleapis/google-auth-library-python/pull/373))
- Update user-guide.rst ([#337](https://github.com/googleapis/google-auth-library-python/pull/337))
- Fix typo in jwt docs ([#332](https://github.com/googleapis/google-auth-library-python/pull/332))
- Clarify which SA has Token Creator role ([#330](https://github.com/googleapis/google-auth-library-python/pull/330))

### Internal / Testing Changes
- Change 'name' to distribution name ([#379](https://github.com/googleapis/google-auth-library-python/pull/379))
- Fix system tests, move to Kokoro ([#372](https://github.com/googleapis/google-auth-library-python/pull/372))
- Blacken ([#375](https://github.com/googleapis/google-auth-library-python/pull/375))
- Rename nox.py -> noxfile.py ([#369](https://github.com/googleapis/google-auth-library-python/pull/369))
- Add initial renovate config ([#356](https://github.com/googleapis/google-auth-library-python/pull/356))
- Use new pytest api to keep building with pytest 5 ([#353](https://github.com/googleapis/google-auth-library-python/pull/353))


## 1.6.3

02-15-2019 9:31 PST

### Implementation Changes

- follow rfc 7515 : strip padding from JWS segments  ([#324](https://github.com/googleapis/google-auth-library-python/pull/324))
- Add retry to `_metadata.ping()` ([#323](https://github.com/googleapis/google-auth-library-python/pull/323))

## 1.6.2

12-17-2018 10:51 PST

### Documentation

- Announce deprecation of Python 2.7 ([#311](https://github.com/googleapis/google-auth-library-python/pull/311))
- Link all the PRs in CHANGELOG ([#307](https://github.com/googleapis/google-auth-library-python/pull/307))

## 1.6.1

11-12-2018 10:10 PST

### Implementation Changes

- Automatically refresh impersonated credentials ([#304](https://github.com/googleapis/google-auth-library-python/pull/304))

## 1.6.0

11-09-2018 11:07 PST

### New Features

- Add `google.auth.impersonated_credentials` ([#299](https://github.com/googleapis/google-auth-library-python/pull/299))

### Documentation

- Update link to documentation for default credentials ([#296](https://github.com/googleapis/google-auth-library-python/pull/296))
- Update github issue templates ([#300](https://github.com/googleapis/google-auth-library-python/pull/300))
- Remove punctuation which becomes part of the url ([#284](https://github.com/googleapis/google-auth-library-python/pull/284))

### Internal / Testing Changes

- Update trampoline.sh ([302](https://github.com/googleapis/google-auth-library-python/pull/302))
- Enable static type checking with pytype ([#298](https://github.com/googleapis/google-auth-library-python/pull/298))
- Make classifiers in setup.py an array. ([#280](https://github.com/googleapis/google-auth-library-python/pull/280))


## 1.5.1

- Fix check for error text on Python 3.7. ([#278](https://github.com/googleapis/google-auth-library-python/pull/#278))
- Use new Auth URIs. ([#281](https://github.com/googleapis/google-auth-library-python/pull/#281))
- Add code-of-conduct document. ([#270](https://github.com/googleapis/google-auth-library-python/pull/#270))
- Fix some typos in test_urllib3.py ([#268](https://github.com/googleapis/google-auth-library-python/pull/#268))

## 1.5.0

- Warn when using user credentials from the Cloud SDK ([#266](https://github.com/googleapis/google-auth-library-python/pull/266))
- Add compute engine-based IDTokenCredentials ([#236](https://github.com/googleapis/google-auth-library-python/pull/236))
- Corrected some typos ([#265](https://github.com/googleapis/google-auth-library-python/pull/265))

## 1.4.2

- Raise a helpful exception when trying to refresh credentials without a refresh token. ([#262](https://github.com/googleapis/google-auth-library-python/pull/262))
- Fix links to README and CONTRIBUTING in docs/index.rst. ([#260](https://github.com/googleapis/google-auth-library-python/pull/260))
- Fix a typo in credentials.py. ([#256](https://github.com/googleapis/google-auth-library-python/pull/256))
- Use pytest instead of py.test per upstream recommendation, #dropthedot. ([#255](https://github.com/googleapis/google-auth-library-python/pull/255))
- Fix typo on exemple of jwt usage ([#245](https://github.com/googleapis/google-auth-library-python/pull/245))

## 1.4.1

- Added a check for the cryptography version before attempting to use it. ([#243](https://github.com/googleapis/google-auth-library-python/pull/243))

## 1.4.0

- Added `cryptography`-based RSA signer and verifier. ([#185](https://github.com/googleapis/google-auth-library-python/pull/185))
- Added `google.oauth2.service_account.IDTokenCredentials`. ([#234](https://github.com/googleapis/google-auth-library-python/pull/234))
- Improved documentation around ID Tokens ([#224](https://github.com/googleapis/google-auth-library-python/pull/224))

## 1.3.0

- Added ``google.oauth2.credentials.Credentials.from_authorized_user_file`` ([#226](https://github.com/googleapis/google-auth-library-python/pull/#226))
- Dropped direct pyasn1 dependency in favor of letting ``pyasn1-modules`` specify the right version. ([#230](https://github.com/googleapis/google-auth-library-python/pull/#230))
- ``default()`` now checks for the project ID environment var before warning about missing project ID. ([#227](https://github.com/googleapis/google-auth-library-python/pull/#227))
- Fixed the docstrings for ``has_scopes()`` and ``with_scopes()``. ([#228](https://github.com/googleapis/google-auth-library-python/pull/#228))
- Fixed example in docstring for ``ReadOnlyScoped``. ([#219](https://github.com/googleapis/google-auth-library-python/pull/#219))
- Made ``transport.requests`` use timeouts and retries to improve reliability. ([#220](https://github.com/googleapis/google-auth-library-python/pull/#220))

## 1.2.1

- Excluded compiled Python files in source distributions. ([#215](https://github.com/googleapis/google-auth-library-python/pull/#215))
- Updated docs for creating RSASigner from string. ([#213](https://github.com/googleapis/google-auth-library-python/pull/#213))
- Use ``six.raise_from`` wherever possible. ([#212](https://github.com/googleapis/google-auth-library-python/pull/#212))
- Fixed a typo in a comment ``seconds`` not ``sections``. ([#210](https://github.com/googleapis/google-auth-library-python/pull/#210))

## 1.2.0

- Added ``google.auth.credentials.AnonymousCredentials``. ([#206](https://github.com/googleapis/google-auth-library-python/pull/#206))
- Updated the documentation to link to the Google Cloud Platform Python setup guide ([#204](https://github.com/googleapis/google-auth-library-python/pull/#204))

## 1.1.1

- ``google.oauth.credentials.Credentials`` now correctly inherits from ``ReadOnlyScoped`` instead of ``Scoped``. ([#200](https://github.com/googleapis/google-auth-library-python/pull/#200))

## 1.1.0

- Added ``service_account.Credentials.project_id``. ([#187](https://github.com/googleapis/google-auth-library-python/pull/#187))
- Move read-only methods of ``credentials.Scoped`` into new interface ``credentials.ReadOnlyScoped``. ([#195](https://github.com/googleapis/google-auth-library-python/pull/#195), [#196](https://github.com/googleapis/google-auth-library-python/pull/#196))
- Make ``compute_engine.Credentials`` derive from ``ReadOnlyScoped`` instead of ``Scoped``. ([#195](https://github.com/googleapis/google-auth-library-python/pull/#195))
- Fix App Engine's expiration calculation ([#197](https://github.com/googleapis/google-auth-library-python/pull/#197))
- Split ``crypt`` module into a package to allow alternative implementations. ([#189](https://github.com/googleapis/google-auth-library-python/pull/#189))
- Add error message to handle case of empty string or missing file for `GOOGLE_APPLICATION_CREDENTIALS` ([#188](https://github.com/googleapis/google-auth-library-python/pull/#188))

## 1.0.2

- Fixed a bug where the Cloud SDK executable could not be found on Windows, leading to project ID detection failing. ([#179](https://github.com/googleapis/google-auth-library-python/pull/#179))
- Fixed a bug where the timeout argument wasn't being passed through the httplib transport correctly. ([#175](https://github.com/googleapis/google-auth-library-python/pull/#175))
- Added documentation for using the library on Google App Engine standard. ([#172](https://github.com/googleapis/google-auth-library-python/pull/#172))
- Testing style updates. ([#168](https://github.com/googleapis/google-auth-library-python/pull/#168))
- Added documentation around the oauth2client deprecation. ([#165](https://github.com/googleapis/google-auth-library-python/pull/#165))
- Fixed a few lint issues caught by newer versions of pylint. ([#166](https://github.com/googleapis/google-auth-library-python/pull/#166))

## 1.0.1

- Fixed a bug in the clock skew accommodation logic where expired credentials could be used for up to 5 minutes. ([#158](https://github.com/googleapis/google-auth-library-python/pull/158))

## 1.0.0

Milestone release for v1.0.0.
No significant changes since v0.10.0

## 0.10.0

- Added ``jwt.OnDemandCredentials``. ([#142](https://github.com/googleapis/google-auth-library-python/pull/142))
- Added new public property ``id_token`` to ``oauth2.credentials.Credentials``. ([#150](https://github.com/googleapis/google-auth-library-python/pull/150))
- Added the ability to set the address used to communicate with the Compute Engine metadata server via the ``GCE_METADATA_ROOT`` and ``GCE_METADATA_IP`` environment variables. ([#148](https://github.com/googleapis/google-auth-library-python/pull/148))
- Changed the way cloud project IDs are ascertained from the Google Cloud SDK. ([#147](https://github.com/googleapis/google-auth-library-python/pull/147))
- Modified expiration logic to add a 5 minute clock skew accommodation. ([#145](https://github.com/googleapis/google-auth-library-python/pull/145))

## 0.9.0

- Added ``service_account.Credentials.with_claims``. ([#140](https://github.com/googleapis/google-auth-library-python/pull/140))
- Moved ``google.auth.oauthlib`` and ``google.auth.flow`` to a new separate package ``google_auth_oauthlib``. ([#137](https://github.com/googleapis/google-auth-library-python/pull/137), [#139](https://github.com/googleapis/google-auth-library-python/pull/139), [#135](https://github.com/googleapis/google-auth-library-python/pull/135), [#126](https://github.com/googleapis/google-auth-library-python/pull/126))
- Added ``InstalledAppFlow`` to ``google_auth_oauthlib``. ([#128](https://github.com/googleapis/google-auth-library-python/pull/128))
- Fixed some packaging and documentation issues. ([#131](https://github.com/googleapis/google-auth-library-python/pull/131))
- Added a helpful error message when importing optional dependencies. ([#125](https://github.com/googleapis/google-auth-library-python/pull/125))
- Made all properties required to reconstruct ``google.oauth2.credentials.Credentials`` public. ([#124](https://github.com/googleapis/google-auth-library-python/pull/124))
- Added official Python 3.6 support. ([#102](https://github.com/googleapis/google-auth-library-python/pull/102))
- Added ``jwt.Credentials.from_signing_credentials`` and removed ``service_account.Credentials.to_jwt_credentials``. ([#120](https://github.com/googleapis/google-auth-library-python/pull/120))

## 0.8.0

- Removed one-time token behavior from ``jwt.Credentials``, audience claim is now required and fixed. ([#117](https://github.com/googleapis/google-auth-library-python/pull/117))
- ``crypt.Signer`` and ``crypt.Verifier`` are now abstract base classes. The concrete implementations have been renamed to ``crypt.RSASigner`` and ``crypt.RSAVerifier``. ``app_engine.Signer`` and ``iam.Signer`` now inherit from ``crypt.Signer``. ([#115](https://github.com/googleapis/google-auth-library-python/pull/115))
- ``transport.grpc`` now correctly calls ``Credentials.before_request``. ([#116](https://github.com/googleapis/google-auth-library-python/pull/116))

## 0.7.0

- Added ``google.auth.iam.Signer``. ([#108](https://github.com/googleapis/google-auth-library-python/pull/108))
- Fixed issue where ``google.auth.app_engine.Signer`` erroneously returns a tuple from ``sign()``. ([#109](https://github.com/googleapis/google-auth-library-python/pull/109))
- Added public property ``google.auth.credentials.Signing.signer``. ([#110](https://github.com/googleapis/google-auth-library-python/pull/110))

## 0.6.0

- Added experimental integration with ``requests-oauthlib`` in ``google.oauth2.oauthlib`` and ``google.oauth2.flow``. ([#100](https://github.com/googleapis/google-auth-library-python/pull/100), [#105](https://github.com/googleapis/google-auth-library-python/pull/105), [#106](https://github.com/googleapis/google-auth-library-python/pull/106))
- Fixed typo in ``google_auth_httplib2``'s README. ([#105](https://github.com/googleapis/google-auth-library-python/pull/105))

## 0.5.0

- Added ``app_engine.Signer``. ([#97](https://github.com/googleapis/google-auth-library-python/pull/97))
- Added ``crypt.Signer.from_service_account_file``. ([#95](https://github.com/googleapis/google-auth-library-python/pull/95))
- Fixed error handling in the oauth2 client. ([#96](https://github.com/googleapis/google-auth-library-python/pull/96))
- Fixed the App Engine system tests.

## 0.4.0

- ``transports.grpc.secure_authorized_channel`` now passes ``kwargs`` to ``grpc.secure_channel``. ([#90](https://github.com/googleapis/google-auth-library-python/pull/90))
- Added new property ``credentials.Singing.signer_email`` which can be used to identify the signer of a message. ([#89](https://github.com/googleapis/google-auth-library-python/pull/89))
- (google_auth_httplib2) Added a proxy to ``httplib2.Http.connections``.

## 0.3.2

- Fixed an issue where an ``ImportError`` would occur if ``google.oauth2`` was imported before ``google.auth``. ([#88](https://github.com/googleapis/google-auth-library-python/pull/88))

## 0.3.1

- Fixed a bug where non-padded base64 encoded strings were not accepted. ([#87](https://github.com/googleapis/google-auth-library-python/pull/87))
- Fixed a bug where ID token verification did not correctly call the HTTP request function. ([#87](https://github.com/googleapis/google-auth-library-python/pull/87))

## 0.3.0

- Added Google ID token verification helpers. ([#82](https://github.com/googleapis/google-auth-library-python/pull/82))
- Swapped the ``target`` and ``request`` argument order for ``grpc.secure_authorized_channel``. ([#81](https://github.com/googleapis/google-auth-library-python/pull/81))
- Added a user's guide. ([#79](https://github.com/googleapis/google-auth-library-python/pull/79))
- Made ``service_account_email`` a public property on several credential classes. ([#76](https://github.com/googleapis/google-auth-library-python/pull/76))
- Added a ``scope`` argument to ``google.auth.default``. ([#75](https://github.com/googleapis/google-auth-library-python/pull/75))
- Added support for the ``GCLOUD_PROJECT`` environment variable. ([#73](https://github.com/googleapis/google-auth-library-python/pull/73))

## 0.2.0

- Added gRPC support. ([#67](https://github.com/googleapis/google-auth-library-python/pull/67))
- Added Requests support. ([#66](https://github.com/googleapis/google-auth-library-python/pull/66))
- Added ``google.auth.credentials.with_scopes_if_required`` helper. ([#65](https://github.com/googleapis/google-auth-library-python/pull/65))
- Added private helper for oauth2client migration. ([#70](https://github.com/googleapis/google-auth-library-python/pull/70))

## 0.1.0

First release with core functionality available. This version is ready for
initial usage and testing.

- Added ``google.auth.credentials``, public interfaces for Credential types. ([#8](https://github.com/googleapis/google-auth-library-python/pull/8))
- Added ``google.oauth2.credentials``, credentials that use OAuth 2.0 access and refresh tokens ([#24](https://github.com/googleapis/google-auth-library-python/pull/24))
- Added ``google.oauth2.service_account``, credentials that use Service Account private keys to obtain OAuth 2.0 access tokens. ([#25](https://github.com/googleapis/google-auth-library-python/pull/25))
- Added ``google.auth.compute_engine``, credentials that use the Compute Engine metadata service to obtain OAuth 2.0 access tokens. ([#22](https://github.com/googleapis/google-auth-library-python/pull/22))
- Added ``google.auth.jwt.Credentials``, credentials that use a JWT as a bearer token.
- Added ``google.auth.app_engine``, credentials that use the Google App Engine App Identity service to obtain OAuth 2.0 access tokens. ([#46](https://github.com/googleapis/google-auth-library-python/pull/46))
- Added ``google.auth.default()``, an implementation of Google Application Default Credentials that supports automatic Project ID detection. ([#32](https://github.com/googleapis/google-auth-library-python/pull/32))
- Added system tests for all credential types. ([#51](https://github.com/googleapis/google-auth-library-python/pull/51), [#54](https://github.com/googleapis/google-auth-library-python/pull/54), [#56](https://github.com/googleapis/google-auth-library-python/pull/56), [#58](https://github.com/googleapis/google-auth-library-python/pull/58), [#59](https://github.com/googleapis/google-auth-library-python/pull/59), [#60](https://github.com/googleapis/google-auth-library-python/pull/60), [#61](https://github.com/googleapis/google-auth-library-python/pull/61), [#62](https://github.com/googleapis/google-auth-library-python/pull/62))
- Added ``google.auth.transports.urllib3.AuthorizedHttp``, an HTTP client that includes authentication provided by credentials. ([#19](https://github.com/googleapis/google-auth-library-python/pull/19))
- Documentation style and formatting updates.

## 0.0.1

Initial release with foundational functionality for cryptography and JWTs.

- ``google.auth.crypt`` for creating and verifying cryptographic signatures.
- ``google.auth.jwt`` for creating (encoding) and verifying (decoding) JSON Web tokens.
