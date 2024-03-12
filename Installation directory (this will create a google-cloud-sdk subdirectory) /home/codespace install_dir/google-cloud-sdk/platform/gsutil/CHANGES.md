Release 5.27 (release date: 2023-10-24)
======================================
New Features
------------------
- Added support for Python 3.12 (#1751)

Other Changes
------------------
- Several documentation updates and clarifications. 

Release 5.26 (release date: 2023-09-21)
======================================
New Features
------------------
- iam ch shim (#1727)
- Adding support for HMAC auth to the shim (#1708)
Add shim support for signurl (#1714)
- Removing alpha from all shim command mappings (#1731)

Bug Fixes
------------------
- Fix typos.
- Formatting fixes.
- Windows parity test fixes (encoding-focused) (#1730)

Other Changes
------------------
- Remove untrusted cert provider (#1741, #1742)

Release 5.25 (release date: 2023-06-21)
======================================
New Features
------------------
- Rsync shim (#1696)
- Adding support for HMAC auth to the shim (#1708)
Add shim support for signurl (#1714)

Bug Fixes
------------------
- Fix SSL missing error by updating Linux Python 3.5 version. (#1692)
- Fix test failures on Linux after docker migration (#1702)
- Updating to include latest boto changes, addressing #1695 (#1715)
- Fixes failing invalid source parent test (#1716)
- Fix dry run mode for signurl shim (#1718)

Other Changes
------------------
- Add warning that shim does not support parallelism override (#1719)
- Update acl.py to use snake case "allUsers" and "allAuthenticatedUsers" (#1720)


Release 5.24 (release date: 2023-05-17)
======================================
New Features
------------------
- Add shim support for du. (#1699)
- Make state directory for mTLS certs configurable. (#1680)

Bug Fixes
------------------
- mTLS: Add support for certificates without passphrase. (#1700)
- Fix SSL missing error by updating Linux Python 3.5 version. (#1692)

Other Changes
------------------
- Update google auth library to latest version. (#1689)
- Several documentation updates and clarifications.
- Several documentation updates and clarifications.

Release 5.24 (release date: 2023-05-17)
======================================
New Features
------------------
- Add shim support for du. (#1699)
- Make state directory for mTLS certs configurable. (#1680)

Bug Fixes
------------------
- mTLS: Add support for certificates without passphrase. (#1700)
- Fix SSL missing error by updating Linux Python 3.5 version. (#1692)

Other Changes
------------------
- Update google auth library to latest version. (#1689)
- Several documentation updates and clarifications.

Release 5.23 (release date: 2023-04-12)
======================================
Other Changes
------------------
- Modified gsutil config to reflect the recent OAuth2 flow deprecation.
- Several documentation updates and clarifications.

Release 5.21 (release date: 2023-03-01)
======================================
New Features
------------------
- Add shim for hmac command (#1670)

Bug Fixes
------------------
- Fix external_account_authorized_user implementation in wrapped_credentials.py + update google-auth dependency (#1674)
- Fix error message for external account authorized user credentials (#1671)
- Handles OAuthException from google-auth (#1672)

Other Changes
------------------
- Several documentation updates and clarifications.

Release 5.20 (release date: 2023-02-02)
======================================
Other Changes
------------------
- Small help updates to acl examples and the cp -j flag (#1667)

Release 5.19 (release date: 2023-01-26)
======================================
Bug Fixes
------------------
- Make reauth check opt-in and silence non-auth-related exceptions. (#1664)
- Fix rpo get shim for s3 buckets (#1659)

Other Changes
------------------
- Several documentation updates and clarifications.

Release 5.18 (release date: 2023-01-12)
======================================
New Features
------------------
- Add shim support for DefAcl get & set (#1654)
- Add shim support for rpo set (#1650)
- Add shim support for the rpo flag in the mb command (#1649)
- Add shim support for ACL commands (#1638)
- Add shim support for custom dual regions (#1645)
- Add shim support for the hash command (#1644)
- Add rsync -y option to compliment -x (#1642)
- Add shim support for retention commands (#1641)
- Add shim support for additional headers (#1634)
- Add shim support for labels commands (#1636)
- Add shim support for CORS commands (#1635)
- Add shim support for IAM commands (#1627)

Bug Fixes
------------------
- Handle reauth challenges gracefully in transfer commands. (#1655)
- Shim gsutil ls behavior of always attempting to fetch hashes. (#1640)

Other Changes
------------------
- Add a warning about the deprecation of the OAuth2 flow. (#1658)
- Several documentation updates and clarifications.

Release 5.17 (release date: 2022-12-01)
======================================
New Features
------------------
- Shim autoclass command (#1618)
- Updating WrappedCredentials to allow for External Account Authorized User Credentials (#1617)

Bug Fixes
------------------
- Fix rsync -x test to address issue #1615 (#1629, #1623)

Other Changes
------------------
- Pin httplib2 to 0.20.4 version (#1628)
- Several documentation updates and clarifications.

Release 5.16 (release date: 2022-10-27)
======================================
New Features
------------------
- Shim lifecycle command. (#1610)
- Shim bucketpolicy only and ubla commands (#1608)
 
Bug Fixes
------------------
- Fixed rsync -x test for Windows and updated docs to match (#1609)
 
Other Changes
------------------
- Update google auth dependency for interactive mode, and url validation (#1614)

Release 5.15 (release date: 2022-10-18)
======================================
Bug Fixes
------------------
- Wildcard iterator should exclude filepaths from rsync -x (#1602)
- Ensure arbitrary headers are included in every rsync request. (#1600)

Other Changes
------------------
- Disable mTLS E2E tests (#1604)

Release 5.14 (release date: 2022-09-22)
======================================
New Features
------------------
- Support including arbitrary headers in requests. (#1598)
- Translate retention flag output for mb shim (#1593)
- Shim cp continue-on-error flag (#1591)
- Add flag for shimming stat. Stop relying on 'run by shim' property. (#1587)

Bug Fixes
------------------
- Update shim get keys (#1595)
- Update google auth dependency (#1581)

Other Changes
------------------
- Update formatting on shim.py (#1597)
- Mb test parity minus retention. (#1592)
- Several documentation updates and clarifications.

Release 5.13 (release date: 2022-09-07)
======================================
New Features
------------------
- Shim now supports mv, compose.
- The version command will now report on whether the shim is being used.

Other changes
------------------
- Shim topic added to additional help.
- Several documentation updates and clarifications.

Release 5.12 (release date: 2022-08-11)
======================================
New Features
------------------
- Allow custom storage class flag for parallel composite upload (#1553)
- Shim requesterpays command (#1552)
- Shim logging command (#1551)
- Shim web command (#1550)
- Shim gsutil rb command (#1549)
- Shim versioning command to gcloud storage (#1544)
- Shim stat command (#1543)

Bug Fixes
------------------
- Update URL for wrapped external creds test (#1568-#1571)
- Update CDR regions to a working pair (#1566)
- Add retries with exponential backoff to the flow that authorizes the service agent to use CMEKs (#1541)
- Fix linter check in shim_util.py (#1546)
- Edit test_nearline_applied_to_parallel_composite_upload so shim passes. (#1558)
- Skip all CDR tests on XML API as there's no way to list placement. (#1556)

Other Changes
------------------
- Increased test parity coverage
- Updated the cat -r command error behavior (#1531)

Release 5.11 (release date: 2022-07-07)
======================================
New Features
------------------
- Bring back placement flag for custom dual regions (#1525)
- Shim rewrite command. (#1537)
- Shim retention object-based subcommands. (#1536)
- Test parity for streaming uploads. (#1533)
- Add pap flag shim support. (#1522)
- Shim support for kms (#1507)
- Update rm shim test parity (#1521)
- Shim cp -I flag (#1520)
- Add shim support for notification commands. (#1518)
- Add shim support for cp ACL flags (#1519)
- Turning off metrics when the shim is enabled. (#1512)
- Add shim support for gzip flags. (#1511)
- Shim translation and test parity for cp manifest flag. (#1497)
- Run by shim env var. (#1510)
- Shim preserve posix (-P) flag. (#1506)

Bug Fixes
------------------
- Added flush to cat\_helper.py (#1528)

Other Changes
------------------
- Replace deprecated threading.currentThread with current\_thread (#1524)
- Updated boto to latest commit
- Several documentation updates and clarifications.

Release 5.10 (release date: 2022-04-26)
======================================
New Features
------------------
- Shim support for defstorageclass (#1494)

Bug Fixes
------------------
- Include Third Party Identification as a Credential Type supporting various use cases (#1501)

Other Changes
------------------
- Several documentation updates and clarifications.

Release 5.9 (release date: 2022-04-07)
======================================
New Features
------------------
- Add cp -v and -n flags for shim translation. (#1490)
- Add cp -s flag to shim translation. (#1488)

Bug Fixes
------------------
- Prevent copies outside of destination directory. (#1491)
- Fix copying duplicate file name conflicts by preserving recursive copy (#1465)

Other Changes
------------------
- Run Python 3.5 tests with 3.5.2 (#1482)
- Backfill the changes required to skip the test\_gsutil tests for gsutil.par tests. (#1481)
- Custom dual region: Drop placement flag as multiple locations can now be provided via -l flag (#1480)
- Several documentation updates and clarifications.

Release 5.8 (release date: 2022-03-07)
======================================
New Features
------------------
- Allow gsutil to transparently call gcloud storage cp or rm through a shim (enable via the Boto configuration GSUTil:use_gcloud_storage=True)
- Allow external account based credentials (#1452)

Bug Fixes
------------------
- Prevent error by only allowing super-user from changing file user when preserve POSIX is enabled. (#1461)

Other Changes
------------------
- Several documentation updates and clarifications.

Release 5.6 (release date: 2022-01-06)
======================================
New Features
------------------
- Check `GCE_METADATA_HOST` environment variable (#1426)
- Allow service account to use private token endpoint (#1417)
- Add default encryption key option (-k) to mb command (#1414)

Bug Fixes
------------------
- PAP: Handle unspecified as well as inherited (#1404)

Other Changes
------------------
- Several documentation updates and clarifications.

Release 5.5 (release date: 2021-11-11)
======================================
Bug Fixes
------------------
- Close upload stream before we try to unlink temp file (#1144)
- Do not perform hash validation if check_hashes=never even if Content-MD5 is set (#1382)

Other Changes
------------------
- Add warning for unsupported double wildcard use. (#1386)
- Changing test email and user references to safer values. (#1396)
- Several documentation updates and clarifications.

Release 5.4 (release date: 2021-10-11)
======================================
New Features
------------------
- Support for new backend features.
- Re-implement removal of project convenience groups (#1365)
- Add suffix to user agent to differentiate between types of rewrite command (#1359)
- mb command: raise error if json only flags are used for xml API  (#1358)
- Improve `gsutil rm` and `gsutil rewrite` help pages. (#1355)
- Link fix and term update in help docs (#1354)

Other Changes
------------------
- Improvements to the Wildcard help topic (#1367)
- Improve `gsutil rm` and `gsutil rewrite` help pages. (#1355)
- Link fix and term update in help docs (#1354)

Release 5.3 (release date: 2021-09-30)
======================================
New Features
------------------
- Add support for Turbo Replication (RPO). (#1351)

Bug Fixes
------------------
- Allow the removal of project convenience groups. (#1350)

Other Changes
------------------
- Several documentation updates and clarifications.

Release 5.2 (release date: 2021-09-23)
======================================
New Features
------------------
- Add cp support for end-to-end encryption via the split-trust encryption tool (STET). (#1338)

Bug Fixes
------------------
- Use custom endpoints for resumable updloads on the XML API. (#1333)

Other Changes
------------------
- Dropped support for Python 2 to patch RSA security issues. (#1339)
- Several documentation updates and clarifications.

Release 4.68 (release date: 2021-09-14)
=======================================
Bug Fixes
------------------
- Improve content type inference for some common extensions. (#1321)
- Copy Content-Encoding from first object in compose command. (#1320)
- Support generation querying for ls command. (#1319)

Other Changes
------------------
- Add a message encouraging py3 upgrade. (#1322)
- Update mock library version. (#1315)
- Several documentation updates and clarifications.

Release 4.67 (release date: 2021-08-16)
=======================================
Bug Fixes
------------------
- Update pyu2f to latest version to fix a security key reauth bug (#1310)

Other Changes
------------------
 - Several documentation updates and clarifications.

Release 4.66 (release date: 2021-07-29)
=======================================
New Features
------------------
 - Onboard mTLS support with AIP-4114 for gsutil (#1302)

Other Changes
------------------
 - Several documentation updates and clarifications.

Release 4.65 (release date: 2021-07-02)
=======================================
New Features
------------------
 - Add gsutil support for Public Access Prevention (#1255)

Bug Fixes
------------------
 - Fix raising-bad-type yapf errors. (#1303)

Other Changes
------------------
 - Link fix pointing to CGC docs again (#1291).
 - Backfill some small doc changes (#1294)
 - Small text tweak (#1293)
 - Update CHECKSUM and VERSION for 4.64 release.
 - Update CHANGES.md for 4.64 release.
 - Delete encryption addhelp page (#1297)
 - Putting cl/381035251 into github (#1296)
 - Backfill cl/381932961 (#1298)

Release 4.64 (release date: 2021-06-18)
=======================================
Bug Fixes
------------------
 - None

Other Changes
------------------
 - Link fix pointing to CGC docs.

Release 4.63 (release date: 2021-06-09)
=======================================
Bug Fixes
------------------
 - Update warning text on KMS access denied (#1278)
 - Make ** to represent zero or more folders for cloud urls (#1277)
 - Raise error if final destination path ends with a delimiter. (#1273)

Other Changes
------------------
 - Fix flaky test for rm using preconditions (#1288)
 - Fix pyenv issue for macOS (#1280)
 - Fix rewrite tests (#1279)
 - Remove unused progress callback. (#1274)
 - Several documentation updates and clarifications.

Release 4.62 (release date: 2021-05-13)
=======================================
New Features
------------------
 - Add ignore-existing option for rsync (#1183).
 - Show satisifiesPZS info in bucket info listing (ls -Lb). (#1191)
 - Support composite uploads with KMS. (#1214)
 - Enforce custom endpoints through multipart copies and complex downloads. (#1247, #1250)

Bug Fixes
------------------
 - rm will continue on object 404s. (#1033)
 - Update boto submodule to include a fix for integrity checks with KMS. (#1258)
 - iam ch is now case-insensitive for public members and member types. (#1241)
 - Support skipping integrity checks in daisy chain transfers. (#1257)
 - Ensure the correct content-length is provided for incomplete downloads. (#1231)
 - Fix daisy chain for windows. (#1251)
 - Fix stats crashing because of nanosecs in custom-time. (#1246)
 - Delete connections after fork. (#1238)
 - Patch md5 import for compliance on Red Hat FIPS mode distributions. (#1224)
 - Handle case where there are too many slashes after CloudUrl scheme. (#1237)
 - Allow specifying object generations in compose. (#1229)
 - Raise error in setmeta if no headers are provided. (#1227)
 - Fix encoding issue for rfc822 messages. (#1234)
 - Fix StreamExhausted Error handling for Resumable uploads. (#1232)
 - Fix wildcard ** bug. (#1235)
 - Fix alignment of ls -l output. (#1219)
 - Fix newlines around lists. (#1220)

Other Changes
------------------
 - Fix sonatype errors. (#1266)
 - gslib: boto\_util: implement a HasUserSpecifiedGsHost() helper. (#1265)
 - Adding warning to rsync if streams or named paths are included in a folder. (#1031)
 - Improve parallelism warnings. (#1226)
 - Several documentation updates and clarifications.

Release 4.61 (release date: 2021-04-06)
=======================================
Bug Fixes
------------------
 - Update to RSA v4.5.
 - CopyHelper accepts kms check bypass. (#1217)

Other Changes
------------------
 - Doc updates.

Release 4.60 (release date: 2021-03-11)
=======================================
Bug Fixes
------------------
 - Fixed proxy connections when using the GCS XML API.
 - Improve reliability when multiple instances of gsutil transfer to the same destination. (#1202)

Other Changes
------------------
 - Remove TravisCI and update "check for CI" references to use GitHub CI. (#1200)
 - Several documentation updates and clarifications.

Release 4.59 (release date: 2021-02-10)
======================================
New Features
------------------
 - Add ignore-existing option for rsync (#1183).
 - Show satisifiesPZS info in bucket info listing (ls -Lb) (#1191).

Bug Fixes
------------------
 - Register integration test failures in kokoro script (#1189).

Other Changes
------------------
 - Use respectful code (#1190).
 - Several documentation updates and clarifications.

Release 4.58 (release date: 2021-01-21)
======================================
Bug Fixes
------------------
 - Fix more occurrences of encodestring/decodestring (#1177)
 - Ignore the .github directory for updates (#1164)
 - Make signurl use generation information. (#1169)
 - Fix UnicodeEncodeError in Python2 for help metadata command (#1172)
 - Open files in non-append mode to make stripe functionality work in Lustre file systems (#1171)
 - Persist request reason header for resumable uploads and downloads. (#1170)
 - improve upload speed significantly when it runs on Windows (#1146)
 - Add perf-trace-token support for resumable uploads. (#1168)
 - Improve error message when a bucket's name collides with another. (#1166)
 - Fix formatting for empty CORS JSON document (#1156)

Other Changes
------------------
 - Several documentation updates and clarifications.
 - Add CI checks for Python 3.8 (#1167)

 Release 4.57 (release date: 2020-12-08)
======================================
Bug Fixes
------------------
 - Remove Unicode character from config command that was causing Python 2 issues.
 - Sync docs with web.

Release 4.56 (release date: 2020-12-03)
======================================
New Features
------------------
 - mTLS/DCA Authentication (#1141, #1122, #1142)
 - Add GitHub Actions CI (#1153)

Bug Fixes
------------------
 - Delete the projects.py help topic (#1154)
 - Format fix for cp.py (#1152)

Release 4.55 (release date: 2020-11-12)
======================================
Bug Fixes
------------------
 - Prevent trailing spaces in json output of iam get (#977)
 - Fix deprecation warnings due to invalid escape sequences. (#1119)
 - Use is_alive in favour of isAlive for Python 3.9 compatibility. (#1121)
 - Fix for base64.{encode/decode}string in python 3.9 (#1129)

Other Changes
------------------
 - Several documentation updates and clarifications.

Release 4.54 (release date: 2020-10-22)
======================================
New Features
------------------
 - Add userProject support to signurl (#1068)

Bug Fixes
------------------
 - Explicitly set multiprocessing start method to 'fork' (#1107)
 - Headers can now be removed (#1091)
 - Fix CommandException.informational attribute error (#1109)
 - Fix broken signurl error message. (#1097)

Other Changes
------------------
 - Warn when disabling parallel composite uploads for KMS encryption. (#1102)
 - Handle SAML reauth challenge. (#1106)
 - Several documentation updates and clarifications.

Release 4.53 (release date: 2020-08-19)
======================================
Bug Fixes
------------------
- Remove socksipy dependency to fix proxy authentication (#1084)
- Retry on errors relating to region specification for S3 (#1049)

Other Changes
------------------
- Prompt Daisy chain users to try STS (#1077)
- Add new IAM types, and disable URL parsing for  IAM b/c it has subcommands. (#1067)
- Many text updates and clarifications.

Release 4.52 (release date: 2020-07-07)
======================================
Bug Fixes
------------------
- Fix tests using wrong AWS credentials if AWS CLI is installed. (#1056)
- Fix `AttributeError: module 'gslib' has no attribute 'USER_AGENT'`. (#1052)
- Fix encoding error in `user_agent_helper`. (#1055)
- Fix stdout ordering issue in hash command. (#1037)
- Fix multithread race condition for cp/mv command when multiple operations are attempting to create the same directory. (#1027)
- Fix OSError on interrupted rsync -d. (#1042)

Other Changes
------------------
- Many text updates and clarifications.

Release 4.51 (release date: 2020-05-19)
======================================
Bug Fixes
------------------
- Fixed file permissions for credstor2 and tracker files (#1002 and # 1005)
- Added a check to restrict the duration (-d option) for signurl command
  to 12 hours if -u flag is used. (#1014)
- Updated rsync command to try patching before overwriting,
  rather than checking ACL (#1016)

Other Changes
------------------
- Several documentation updates and clarifications.

Release 4.50 (release date: 2020-04-30)
======================================
New Features
------------------
- Switched to Using V4 signature as default for S3 (#981)

Bug Fixes
------------------
- Updated rsa library to release-4.0 (#992)
- Updated test script to install pyenv if missing for kokoro (#990)
- Fixed print ordering in kms set by using print instead of
  text_util.print_to_fd (#974)

Other Changes
------------------
- Several documentation updates and clarifications (#969) (#987)

Release 4.49 (release date: 2020-03-26)
======================================
New Features
------------------
- Added support for service account impersonation for signurl.

Bug Fixes
------------------
- Fixed an issue with rsync throwing error when the destination url is a prefix of
  an existing object.

Other Changes
------------------
- Several documentation updates and clarifications.

Release 4.48 (release date: 2020-02-28)
======================================
Bug Fixes
------------------
- Fixed special character handling in filenames on Windows with Python3.
- Fixed issue while transferring binary files from S3 with Python3.
- Fixed KMS tests, so that keys are created in the same region as their buckets.

Other Changes
------------------
- Several documentation updates and clarifications.

Release 4.47 (release date: 2020-01-10)
======================================
New Features
------------------
- Added support for the new archive storage class.

Other Changes
------------------
- Several documentation updates and clarifications.

Release 4.46 (release date: 2019-10-31)
=======================================
Bug Fixes
------------------
 - Fixed issue with domain permissions functionality.

Release 4.45 (release date: 2019-10-18)
=======================================
Bug Fixes
------------------
 - Fixed exception when using CMEK with resumable uploads.
 - Fixed alias for new ubla command.
 - Fixed default RDNS behavior for backwards compatibility with 4.42 and earlier.

Other Changes
------------------
- Improvements to continuous integration workflow.

Release 4.44 (release date: 2019-10-02)
=======================================
New Features
------------------
- Added support for service account impersonation through a new `-i` option to
  specify a service account to impersonate.
- Added support for members using the deleted syntax (i.e. `deleted:user:...`,
  `deleted:group:...`, `deleted:serviceAccount:...`).
- Added support for the new uniform bucket-level access (`ubla`) command
  (currently an alias of `bucketpolicyonly`).
- Added `-w` flag to `kms` command, which shows a warning rather than failing
  when updating key permissions does not succeed.

Bug Fixes
------------------
- Fixed regression in cp where a statement like
  `cp my-file gs://my-bucket/non-existent-folder/` would create a file called
  `non-existent-folder` rather than `non-existent-folder/my-file`.
- Fixed streaming uploads for Python 3.


Release 4.43 (release date: 2019-09-20)
=======================================
New Features
------------------
- Added support for socks proxies, including socks4 and socks5.

Bug Fixes
------------------
- Fixed cp/mv errors that occur when  destination directory is a substring of
  another directory. Behavior now more closely matches OS cp/mv commands.
- Fixed issue where set IAM policy on objects threw errors.
- Fixed issue when showing help in a pager in Python 3 environments.

Other Changes
------------------
- Several documentation updates and clarifications.

Release 4.42 (release date: 2019-08-05)
=======================================
 Bug Fixes
------------------
- Fixed some text encoding/decoding issues in certain Python 3 environments.
- Fixed issue where bundled crcmod for macOS could not be imported and would
  crash gsutil on Python 3.
- Fixed issue where trying to run gsutil on an unsupported version of Python 3
  (3.4 or below) would crash instead of presenting an informative error.

Other Changes
------------------
- Several documentation updates and clarifications.


Release 4.41 (release date: 2019-07-16)
=======================================
New Features
------------------
- Added HMAC key management for service accounts. This includes a new "hmac"
  command to create/get/list/update/delete HMAC keys on service accounts.
  Currently, your project must be added to the allowlist for use with this new HMAC
  functionality. This restriction will be lifted in the near future.

 Bug Fixes
------------------
- Fixed bug where copying files > 100MiB from GCS to S3 was hanging.
- Fixed issue where content type was sometimes set improperly.


Release 4.40 (release date: 2019-07-01)
=======================================
New Features
------------------
- Added support for running gsutil on Python 3.5+. Python 2 will reach its EOL
  (End of Life) on Jan. 1, 2020, and gsutil will stop supporting Python 2.7 at
  some point afterward (TBD).

 Bug Fixes
------------------
- Fixed bug introduced in v4.39 where rsync would not correctly sync object/file
  names containing some special URL-encodable characters (e.g. "+" and
  whitespace characters).
- Fixed the update command so that it no longer fails when it detects the
  presence of additional top-level files that were added in the v4.39 release.

 Other Changes
------------------
- Several documentation updates and clarifications.


Release 4.39 (release date: 2019-06-13)
=======================================
New Features
------------------
- Compression level is now configurable by setting "gzip_compression_level"
  under the "GSUtil" section in the boto config file. The default value is 9.

 Bug Fixes
------------------
- Fixed bug where IAM operations failed on buckets whose names lacked any
  letters.

 Other Changes
------------------
- Revised contribution guidelines to direct developers to submit GitHub pull
  requests instead of using the Rietveld code review tool.
- Several code changes to work toward Python 3 support (coming in a subsequent
  release).
- Several documentation and command help improvements.
- Various improvements to test stability and feedback.


Release 4.38 (release date: 2019-03-25)
=======================================
Bug Fixes
------------------
- Fixed issue where multiprocessing check would raise an exception if
  /etc/os-release was not in the expected format.

Other Changes
------------------
- Improved error message for trying to retrieve default object ACLs on a bucket
  with Bucket Policy Only enabled.
- When running "gsutil -D rsync ..." and encountering an error listing local
  files, gsutil will now print a stack trace as debug-level output.
- Several documentation updates and clarifications.


Release 4.37 (release date: 2019-02-26)
=======================================
Bug Fixes
------------------
- Fixed a bug where XML API requests would sometimes fail with SSLError
  exceptions due to SNI not being used for https connections.
- Fixed "du" output spacing for 6-digit sizes.

Other Changes
------------------
- Updated crcmod installation instructions for CentOS 6.


Release 4.36 (release date: 2019-01-28)
=======================================
New features
------------------
- Added Bucket Policy Only support to gsutil. This includes a new
  "bucketpolicyonly" command to get/set BPO on existing buckets, as well adding
  the ability to set BPO at bucket creation time with "mb -b". Currently, your
  project must be added to the allowlist for use with the new BPO functionality.
  This restriction will be lifted in the near future.

Bug Fixes
------------------
- Fixed a bug where "cp -n" would overwrite a local file at the destination if
  its size differed from the source's size.

Other Changes
------------------
- Updated crcmod installation instructions for enterprise SUSE systems.


Release 4.35 (release date: 2018-12-18)
=======================================
New features
------------------
- Added -u option to rsync; this will skip copying files/objects that are newer
  (as determined by checking mtime) at the destination.

Bug Fixes
------------------
- The "iam ch" command now allows supplying custom IAM roles.
- Fixed an issue where debug output was not displaying all of the loaded config
  files under the "config path(s)" label.
- Disabled running with multiple processes when running on Alpine Linux, as this
  would sometimes cause gsutil to hang forever. Running with multiple threads is
  still allowed.
- The "rsync" command now prints log messages during synchronization to indicate
  when symlinks are being skipped.
- The "Boto:ca_certificates_file" config option can now be overridden using
  the -o option.

Other Changes
------------------
- Disallowed installing gsutil on Python versions != 2.7.
- Several documentation updates and clarifications.


Release 4.34 (release date: 2018-09-11)
=======================================
New features
------------------
- Added bucket lock support to gsutil. Currently, your project must be added to
  the allowlist for use with the new bucket lock functionality. This restriction
  will be lifted in the near future.

Bug Fixes
------------------
- Fixed issue where "rsync -P" would fail if run as the root user.
- Fixed an issue with credential caching where the source credentials for an
  entity would change but the old cached credentials would still be used.

Other Changes
------------------
- OAuth2 token exchanges now go to https://oauth2.googleapis.com/token instead
  of https://accounts.google.com/o/oauth2/token. Users using gsutil behind a
  firewall may need to adjust their firewall rules.
- If invoked via the Cloud SDK, gsutil's debug output now displays the path to
  gcloud's gsutil wrapper script for "gsutil path", rather than the actual entry
  point for the bundled gsutil component.
- Improved error messages for failed Cloud KMS requests.
- Improved error messages for "iam ch" command to clarify that assigning
  roles to project convenience groups (e.g. "projectEditor") is not allowed.
- Enhanced perfdiag command to include GCE instance details (if applicable)
  and the target bucket's location and storage class.
- Several documentation updates and clarifications.


Release 4.33 (release date: 2018-06-21)
=======================================
Bug Fixes
------------------
- Fixed an issue with the "rsync" command on Windows that would cause gsutil
  to incorrectly join file path segments when the source given was the root
  of a drive, e.g. "C:".
- Fixed several places where gsutil referenced a variable that had not been
  correctly imported.

Other Changes
------------------
- Several documentation updates and clarifications.


Release 4.32 (release date: 2018-06-01)
=======================================
Bug Fixes
------------------
- Fixed a file path resolution issue on Windows that affected local-to-cloud
  copy-based operations ("cp", "mv", "rsync"). If a local file URI containing
  relative path components ("." or "..") or forward slashes (rather than
  backslashes) was provided as a source argument, the resulting destination
  object(s) was incorrectly named. For recursive operations, this resulted in
  several files being copied to the same object path, overwriting each other.
- Fixed an issue with the "rsync" command on Windows that resulted in each rsync
  invocation not being able to delete its temporary synchronization files on
  disk.
- Fixed an issue where reading a specific generation of an object from S3 would
  fail.
- Fixed an issue where running gsutil with the top-level "-q" flag would result
  in credential-related logging statements being emitted to stderr.
- Gsutil no longer allows copying from streamed input if the top-level "-m" flag
  is specified. While this was previously allowed, it did not work correctly.

Other Changes
------------------
- Several documentation updates and clarifications.


Release 4.31 (release date: 2018-04-26)
=======================================
New features
------------------
- Added support for reauthentication within gsutil. Note that this only affects
  authentication when "gs_oauth2_refresh_token" is configured under the
  "Credentials" section of the boto config file and that token corresponds to a
  user account enrolled in 2-step verification.

Bug Fixes
------------------
- When creating a signed URL via the "signurl" command, gsutil now verifies that
  the specified expiration isn't longer than 7 days (the maximum allowed by the
  service).
- To support rewriting objects to be encrypted using a bucket's default KMS key,
  the "rewrite" command now rewrites all specified objects if no value is
  specified for "encryption_key" under the "GSUtil" section in the boto config
  file.

Other Changes
------------------
- Several documentation updates and clarifications.


Release 4.30 (release date: 2018-03-28)
=======================================
New features
------------------
- Added Cloud KMS support for Google Cloud Storage resources, allowing the use
  of customer-managed encryption keys (CMEKs). Bucket-related functionality
  includes the new "kms" command, which can be used to get or set a bucket's
  default KMS key. Concerning objects, users may now specify the CMEK to be used
  for encryption via their boto config file, in the "encryption_key" attribute.
  In this way, users may specify either a CSEK or a CMEK to encrypt new objects,
  but not both. For more information, see "gsutil help encryption".

Other Changes
------------------
- Several documentation updates and clarifications.


Release 4.29 (release date: 2018-03-14)
=======================================
New features
------------------
- Added transport compression support, available through the "-j" and "-J"
  options for the "cp", "mv", and "rsync" commands. This is useful when
  uploading files with highly-compressible content. When specificed, files being
  uploaded are compressed on-the-fly in memory, sent to GCS, and uncompressed by
  GCS before they are stored. See "gsutil help cp" for additional information.
- When "use_magicfile=True" is set in the boto config file, gsutil will now
  append the detected charset, if present, to the object's Content-Type metadata
  field. For example, a Content-Type might be populated with
  "text/html; charset=us-ascii" rather than simply "text/html".

Bug Fixes
------------------
- Improved error handling and logging for upload resumption.
- After encountering a PreconditionException, the "acl ch" command will now
  re-fetch the object generation before retrying.
- Fixed issue with parsing lifecycle conditions when using the XML API.
  Conditions whose values could be evaluated by Python as "falsy" (e.g. setting
  an "age" condition to the number 0 or "isLive" to false) would be omitted from
  the lifecycle configuration when "prefer_api=xml" was set in the boto config
  file. Note that the JSON API is preferred by default, so most users were
  unlikely to encounter this issue.
- For commands that fetch bucket ACLs or default ACLs, when the user does not
  have storage.buckets.getIamPolicy on the GCS bucket, using the XML API will
  now behave consistently with the JSON API and display ACL/default ACL fields
  as empty, rather than throwing a CommandException.

Other Changes
------------------
- Several documentation updates and clarifications.
- The "signurl" command now uses signature V4 signing format to generate URLs.


Release 4.28 (release date: 2017-10-11)
=======================================
New features
------------------
- Added newest version of the Boto library, which includes support for using
  Signature Version 4 to connect to S3 buckets via the "use-sigv4 = True" and
  "host = s3.<region>.amazonaws.com" Boto options under the "[s3]" section.
- Added support for Requester Pays functionality when making requests to GCS
  buckets with this feature enabled. For example usage, see the entry for "-u"
  in "gsutil help options". Requester Pays is currently only supported for
  requests using the GCS JSON API; XML API support will be added in a later
  version.

Bug Fixes
------------------
- Fixed issue where attempting to preserve ACLs by using "-p" with cp/mv/rsync
  would fail when the destination is a local file.
- Improved quality of several ambiguous error messages.

Other Changes
------------------
- The proxy_rdns option is now True by default when a proxy is set. Also added
  Boto config file comments explaining that gcloud proxy options, if present,
  take precedence over corresponding Boto settings and environment variable
  settings.
- Following the deprecation of Python 2.6 support for gsutil, code sections that
  were only present to support Python 2.6 have been removed.
- Several documentation updates and clarifications.


Release 4.27 (release date: 2017-06-29)
=======================================
New features
------------------
- When using the JSON API, the "ls -L" and "stat" commands now print an object's
  storage class update time if it differs from the object's creation time; this
  occurs when the storage class has been changed due to the bucket's lifecycle
  management configuration.
- Listing a bucket's metadata via "ls -Lb" now prints its metageneration.

Bug Fixes
------------------
- When specifying custom metadata values using the top-level -h option, such
  values may now include unicode characters as well as multiple ":" characters.
- For Cloud SDK (gcloud) distributions of gsutil, if you have configured the
  Cloud SDK to not pass credentials to gsutil (by running "gcloud config set
  pass_credentials_to_gsutil false"), gsutil will now correctly work with
  credentials obtained via "gsutil config". This would previously result in an
  error with a message to run "gcloud auth login". Additionally, the "gsutil
  config" command no longer prompts users to run "gcloud auth login" if this
  option is set to false. This should allow switching between stand-alone
  gsutil installations and gcloud-packaged gsutil installations more easily.
- The config_file_list section in debug output now displays files in the order
  that they are loaded.

Other Changes
------------------
- Added XML support for some commands which previously only worked via the JSON
  API ("lifecycle" and "defstorageclass").
- Several documentation updates and clarifications.


Release 4.26 (release date: 2017-05-03)
=======================================
New features
------------------
- The cp command now supports reading from and writing to named pipes.

Bug Fixes
------------------
- Fixed issue where tab completion wasn't working.
- Fixed issue when using the XML API where gsutil would fail to parse bucket
  metadata for buckets using Lifecycle rules containing the SetStorageClass
  action or MatchesStorageClass condition.

Other Changes
------------------
- Removed -o flag from "notification create" command. The same functionality is
  available with the -p flag; the -o flag had been mistakenly added in a
  previous change.
- Removed the alpha disclaimer from the iam command help text.
- Several documentation updates and clarifications.


Release 4.25 (release date: 2017-04-05)
=======================================
New features
------------------
- Added bucket label support to gsutil. For more details, see
  https://cloud.google.com/compute/docs/label-or-tag-resources.
- Added the label command, which can be used to get, set, and change the labels
  for an existing bucket (known as "tags" for S3 buckets).
- Listing a bucket via "gsutil ls -Lb" now also displays the labels, if any
  exist, that are currently set on it.


Release 4.24 (release date: 2017-03-27)
=======================================
New Features
------------------
- Added support for configuring GCS Cloud Pub/Sub notifications. For more
  details, see https://cloud.google.com/storage/docs/pubsub-notifications.
- Added support for specifying canned ACLs when using the rsync command.

Bug Fixes
------------------
- Fixed a bug where error messages about invalid object names did not correctly
  display the problematic object name.


Release 4.23 (release date: 2017-03-09)
=======================================
Bug Fixes
------------------
- Fixed "referenced before assignment" error in some copy_helper exceptions for
  resumable uploads and non-resumable cloud-to-local downloads.
- The setmeta command now properly supports case sensitivity in custom metadata
  keys when using the JSON API.
- Fixed a resource leak affecting Windows in cases where single-process,
  multithreaded parallelism is used that would result in an OSError with the
  message "Too many open files".
- Fixed HTTPError initialization failure in signurl command.
- Fixed signurl issue where attempting to validate short-lived URLs on a slow
  connection would fail because of URL expiration.
- Fixed a bug where cp -r would not properly resolve wildcards for
  cloud-to-cloud copies.
- Fixed a bug where cp -e -r would copy symlinks.
- Fixed a bug where cp -P would fail on Windows.
- Fixed a bug where version -l might not show all boto configuration files.
- Running perfdiag now only lists the objects that were created by that run of
  perfdiag. This fixes an issue where running perfdiag against an existing
  bucket with many objects in it could take a long time.


Other Changes
------------------
- Simplified parallelism when using a single process with multiple threads.
  With this change, gsutil will spawn a new thread pool per level of
  parallelism. As an example, if you specify that you want a
  parellel_thread_count of 24, this will result in 24 worker threads, except
  when you're using parallel composite uploads or sliced downloads, in which
  case 48 (24 * 2) worker threads will be used.
- Extended the early deletion warning threshold when moving Coldline objects
  to 90 days after object creation.
- Improved several error messages and warnings.
- Several documentation updates and clarifications.

Release 4.22 (release date: 2016-10-20)
=======================================
New features
------------------
- Added per-object storage class functionality to gsutil. For more details, see
  https://cloud.google.com/storage/docs/per-object-storage-class.
- Added the defstorageclass command, which can be used to get and set an
  existing bucket's default storage class.
- The cp, mv, and rewrite commands now support the "-s" option, allowing users
  to specify the storage class for destination object(s). When no storage class
  is specified, the object's storage class will be assigned from either its
  bucket's default storage class (cp/mv commands) or the source object's
  storage class (rewrite command).

Bug Fixes
------------------
- Fixed a bug in POSIX preservation for the cp and mv commands where POSIX
  attributes were not propagated to cloud objects, even when the -P flag was
  present.
- Fixed a bug in setmeta where removing custom metadata would add an
  empty-string value if the key did not already exist.
- Content-Type is now obtained from symlink targets, rather than symlinks
  themselves, when the use_magicfile option is set in the .boto configuration
  file.

Other Changes
------------------
- Analytics reporting now includes performance metrics such as average
  throughput and thread idle time.
- The iam set command now supports a -e option to specify an etag precondition
  check. The IAM policy file returned by iam get and used by iam set has also
  been altered to include this field.
- Default limit for max number of processes changed to 64.
- Several documentation updates and clarifications.

Release 4.21 (release date: 2016-08-16)
=======================================
New Features
------------------
- The console output for many commands has been improved to display
  command progress.
- The cp, mv, and rsync commands now support a -P option that preserves
  POSIX file attributes from the source. Currently, mode, gid, uid,
  atime, and mtime attributes are supported for uploads, downloads,
  and copies.
- gsutil can now optionally report anonymous usage statistics that help
  gsutil developers improve the tool. For non-gcloud distributions,
  prompts have been added to the config and update commands. Prompts can
  be disabled via the disable_analytics_prompt value in the .boto
  configuration file.
- Added the iam commmand, which can be used to set IAM policies on
  Google Cloud Storage buckets and objects. This feature is currently in
  alpha and requires a safelist application to use it - see
  "gsutil help iam" for  details.
- The hash command now supports retrieving hashes for cloud objects.

Bug Fixes
------------------
- Fixed a bug where rsync -e -r could fail for subdirectories with
  broken symlinks.
- Fixed an access error when interacting with S3 user-specific
  directories.

Other Changes
------------------
- Updated boto library dependency to 2.42.0.

Release 4.20 (release date: 2016-07-20)
=======================================
New Features
------------------
- gsutil now outputs a message that estimates the total number of objects for
  commands affecting more than 30,000 objects. This value can be adjusted via
  task_estimation_threshold in the .boto configuration file.

Bug Fixes
------------------
- Fixed a bug in resumable downloads that could raise UnboundLocalError if
  the download file was not readable.
- Updated oauth2client to version 2.2.0, fixing some IOError and OSError cases.
- Fixed bug in gsutil ls that would show update time instead of creation
  time when using the JSON API and -L or -l flags.
- Fixed a bug in gsutil rsync -d that could cause erroneous removal of
  an extra destination object.
- Fixed downloads to include accept-encoding:gzip logic when appropriate.

Other Changes
------------------
- gsutil rsync now stores modification time (mtime) for cloud objects.
- Changed the default change detection algorithm of gsutil rsync from file
  size to file mtime, falling back to checksum and finally file
  size as alternatives. This allows for increased accuracy of rsync without
  the speed sacrifice that comes from checksum calculation, and makes gsutil
  rsync work more similarly to how Linux rsync works. Note that the first
  run of a local-to-cloud rsync using this new algorithm may be slower than
  subsequent runs, as the cloud objects will not initially have an mtime, and
  the algorithm will fall back to the slower checksum-based alternative in
  addition to adding mtime to the cloud objects.
- When using the JSON API, gsutil will output a progress message before
  retrying a request if enough time has passed since the first attempt.
- Improved error detection in dry runs of gsutil rsync by attempting to open
  files that would be copied.
- Added time created and time updated properties to output of gsutil ls -Lb.
- Added archived time property to output of gsutil ls -La and gsutil stat.
- Changed minimum number of source objects for gsutil compose from 2 to 1.
- Removed an HTTP metadata get call from cp, acl, and setmeta commands. This
  improves the speed of gsutil cp for small objects by over 50%.
- Several documentation updates and clarifications.

Release 4.19 (release date: 2016-04-13)
=======================================
Deprecation Notice
------------------
- gsutil support for Python 2.6 is deprecated, and gsutil will stop
  supporting Python 2.6 on September 1, 2016. This change is
  being made for two reasons. First, Python 2.6 stopped
  receiving security patches since October 2013. Second,
  removing Python 2.6 support will enable gsutil to add support
  for Python 3. Versions of gsutil released prior to September 1,
  2016 will continue to work with Python 2.6. However, bug fixes
  will not be made retroactively to older gsutil versions, and users
  reporting bugs will be asked to upgrade to the current gsutil
  version (using Python 2.7, or, when it is supported, Python 3).

Other Changes
-------------
- Improved documentation around Cloud SDK (gcloud) installs.

Release 4.18 (release date: 2016-03-22)
=======================================
New Features
------------
- gsutil now supports the beta Customer-Supplied Encryption Keys
  features for Google Cloud Storage objects, via the JSON API.
  This feature allows you to encrypt your data with keys that
  are not permanently stored on Google's servers. You can provide
  encryption and decryption keys in your .boto configuration file.
  As long as an encryption key is specified in the configuration file,
  all gs:// objects that gsutil creates will be stored encrypted
  with that key, and all encrypted objects will be decrypted when
  downloaded. See "gsutil help csek" for more information.
- Added the rewrite command, which can be used to perform
  key rotation for objects encrypted with customer-supplied
  encryption keys.

Bug Fixes
---------
- Fixed an AttributeError that could occur when running in debug mode
  for operations involving wildcards, recursion, or listing.
- Fixed an ArgumentException that could occur when using perfdiag
  write throughput tests with parallelism.
- Restored debug mode output for resumable uploads using the JSON API.
- Fixed a bug where rm -r on a bucket subdirectory would exit with
  code 1 even though it succeeded.
- Fixed a bug where cp -R of a single file with a destination other
  than the bucket root would copy to the bucket root.
- Fixed a bug when using a single process with multiple threads
  where CTRL-C would not stop the process until one thread completed
  a task.

Other Changes
-------------
- Improved exception logging in debug mode.
- Added "cache-control: no-transform" to all uploads
  using compression ("gsutil cp -z" or "gsutil cp -Z") to ensure that
  doubly-compressed objects can be downloaded with data integrity
  checking.
- Reduced the default number of threads per-process on Linux systems
  from 10 to 5.
- Documented additional OS X Unicode limitations.
- The config command now includes the custom client ID and secret in the
  configuration file output if the command is run with those values
  configured.

Release 4.17 (release date: 2016-02-18)
=======================================
Bug Fixes
---------
- Fixed an oauth2client dependency break that caused
  the PyPi distribution of gsutil to allow oauth2client 2.0.0,
  causing all commands to fail with an ImportError.
- Fixed a bug where gsutil could leak multiprocessing.Manager
  processes when terminating signals (such as CTRL-C) were sent.
- Fixed a bug where the -q option did not suppress output
  from the stat command.
- Fixed a bug where deleting an empty bucket with rm -r
  would return a non-zero exit code even when successful.
- Fixed UnicodeEncodeErrors that could occur when using the du
  command with a pipe on objects containing non-ASCII characters.

Other Changes
-------------
- Many documentation improvements and clarifications.

Release 4.16 (release date: 2015-11-25)
=======================================
New Features
------------
- The ls command now supports a -d option (similar to Unix ls -d)
  for suppressing recursion into subdirectories.
- The signurl command now accepts JSON-format private key files
  generated by the Google Developers Console.
- The signurl command now supports generating resumable upload
  start URLs.
- The cp command now supports a -Z option which will gzip-compress all
  files (regardless of their extensions) as they are uploaded.

Bug Fixes
---------
- Fixed a bug where an expired OAuth2 token could include the OAuth2
  token response as part of the download, causing it to fail end-to-end
  integrity checks and be deleted.
- Fixed a bug where streaming downloads using the JSON API would restart
  from the beginning of the stream if the connection broke. This bug
  could also cause data corruption in streaming downloads, because
  streaming downloads are not validated with end-to-end integrity checks.
- Fixed an internal_failure exception that could occur when an OAuth2
  token refresh returned a transient error, such as an HTTP 503.
- Fixed a resource deadlock exception in oauth2client that could cause
  sliced downloads to hang.
- Fixed a bug where cp/rsync -p would use the default object
  ACL for the destination object if the caller did not have OWNER
  permission on the source object.
- Fixed a potential race condition when using perfdiag with multiple
  threads and/or processes.
- Fixed an AttributeError that could occur when using acl ch -p.
- Fixed a bug where the mv command did not properly handle the global
  -m flag.
- Fixed a UnicodeEncodeError that could occur when iterating over
  non-Unicode-named directories.
- Fixed a bug where an object name including a wildcard could cause
  an infinite loop during a recursive listing.
- Fixed a Unicode bug when using cp or ls on Windows on an object
  containing certain Unicode characters. However, even with this fix
  Unicode can still be problematic on Windows; consult
  "gsutil help encoding" for details.
- Fixed a Windows performance issue during rsync diff generation.
- Fixed a bug in the ordering of ls output.
- Fixed a bug where Windows help output included ANSI escape codes.
- Fixed a compatibility bug with perfdiag -i with input generated prior
  to gsutil 4.14.

Other Changes
-------------
- Several documentation updates, including rsync exclusion pattern matching,
  service account configuration, cp/rsync recursion flags, multi-object rm,
  versioned URL removal, destination subdirectory naming, wildcard behavior,
  regional buckets, and s3 connection reset.
- Improvements to Unicode documentation including LANG variable and iconv
  tool.

Release 4.15 (release date: 2015-09-08)
=======================================
Bug Fixes
---------
- Fixed an OverflowError in apitools that caused download
  failures for large files on 32-bit machines.
- Removed unnecessary sending of range headers for downloads when
  using the XML API.
- Fixed a bug that caused perfdiag to report extremely high throughput
  when the -p flag was unspecified and exactly one of the -c or -k flags
  were specified.
- Fixed a ValueError that occurred on Python 2.6 with sliced object downloads.

Other Changes
-------------
- HTTP connections for downloads and uploads in the JSON API are now
  re-used per-thread.
- When gsutil's automatic update feature prompts and the user
  chooses to update, gsutil will now exit with status code 1 after
  updating (because the original command was not executed).
- The cp -A flag is disabled when using gsutil -m to ensure that
  ordering is preserved when copying between versioned buckets.

Release 4.14 (release date: 2015-08-24)
=======================================
New Features
------------
- Implemented Sliced Object Download feature.
  This breaks up a single large object into multiple pieces and
  downloads them in parallel, improving performance. The gsutil cp, mv
  and rsync commands now use this by default when compiled crcmod
  is available for performing fast end-to-end integrity checks.
  If compiled crcmod is not available, normal object download will
  be used. Sliced download can be used in conjunction with the global -m
  flag for maximum performance to download multiple objects in
  parallel while additionally slicing each object.
  See the "SLICED OBJECT DOWNLOAD" section of "gsutil help cp" for
  details.
  Note: sliced download may cause performance degradation for disks
  with very slow seek times. You can disable this feature by setting
  sliced_object_download_threshold = 0 in your .boto configuration file.
- Added rthru_file and wthru_file test modes to perfdiag, allowing
  measurement of reads and writes from a disk. This also allows
  measurement of transferring objects too large to fit in memory.
  The size restriction of 20GiB has been lifted.
- perfdiag now supports a -p flag to choose a parallelism strategy
  (slice, fan, or both) when using multiple threads and/or processes.

Bug Fixes
---------
- Fixed an IOError that could occur in apitools when acquiring credentials
  using multiple threads and/or processes on Google Compute Engine.
- Fixed a bug where rm -r would attempt to delete a nonexistent bucket.
- Fixed a bug where a default object ACL could not be set or changed to empty.
- Fixed a bug where cached credentials corresponding to an old account could
  be used (for example, credentials associated with a prior .boto
  configuration file).
- Fixed a bug in apitools for retrieving byte ranges of size 1 (for example,
  "cat -r 1-1 ...")
- Fixed a bug that caused the main gsutil process to perform all work leaving
  all gsutil child processes idle.
- Fixed a bug that caused multiple threads not to be used when
  multiprocessing was unavailable.
- Fixed a bug that caused rsync to skip files that start with "." when the
  -r option was not used.
- Fixed a bug that caused rsync -C to bail out when it failed to read
  a source file.
- Fixed a bug where gsutil stat printed unwanted output to stderr.
- Fixed a bug where a parallel composite upload could return a nonzero exit
  code even though the upload completed successfully. This occurred if
  temporary component deletion triggered a retry but the original request
  succeeded.
- Fixed a bug where gsutil would exit with code 0 when both running in
  debug mode and encountering an unhandled exception.
- Fixed a bug where gsutil would suggest using parallel composite uploads
  multiple times.

Other Changes
-------------
- Bucket removal is now supported even if billing is disabled for that bucket.
- Refactored Windows installs to no longer use any multiprocessing module
  functions, as gsutil has never supported multiple processes on Windows.
  Multithreading is unaffected and still available on Windows.
- All downloads are now written to a temporary file with a "_.gstmp" suffix
  while the download is still in progress.
- Re-hashing of existing bytes when resuming downloads now displays progress.
- Reduced the total number of multiprocessing.Manager processes to two.
- The rm command now correctly counts the number of objects that could
  not be removed.
- Increased the default retries to match the Google Cloud Storage SLA.
  By default, gsutil will now retry 23 times with exponential backoff up
  to 32 seconds, for a total timespan of ~10 minutes.
- Improved bucket subdirectory checks to a single HTTP call. Detection of
  _$folder$ placeholder objects is now eventually consistent.
- Eliminated two unnecessary HTTP calls when performing uploads via
  the cp, mv, or rsync commands.
- Updated documentation for several topics including acl, cache-control,
  crcmod, cp, mb, rsync, and subdirs.
- Added a warning about using parallel composite upload with NEARLINE
  storage-class buckets.

Release 4.13 (release date: 2015-06-03)
=======================================
New Features
------------
- Added -U flag to cp and rsync commands to allow skipping of unsupported
  object types.
- Added support for Google Developer Shell credentials.

Bug Fixes
---------
- Precondition headers (x-goog-if-...) are now respected for the setmeta
  command.
- Fixed an index out of range error that could occur with an empty
  parallel composite upload tracker file.
- The stat command outputs errors to stderr instead of stdout.
- Fixed two possible sources of ResumableUploadStartOverException from
  httplib2 and oauth2client.
- Fixed a bug in the compose command where a missing source object resulted
  in an error message claiming the destination object was missing.

Other Changes
-------------
- Added a help section on throttling gsutil.
- Resumable uploads will now start over if a PUT to the upload ID returns
  an HTTP 404. Previously this behavior applied only to an HTTP 410.
- XML API resumable uploads now retry on HTTP 429 errors, matching the
  behavior of JSON API resumable uploads.
- Improved response to process kill signals, reducing the likelihood of
  leaving orphaned child processes and temporary files.
- Bucket lifecycle configuration now works for S3.
- Removed the deprecated setmeta -n option.


Release 4.12 (release date: 2015-04-20)
=======================================
New Features
------------
- Added support for JSON-format service account private key files.
- Added support for the Rewrite API (JSON API only). This is used for
  all copies within the Google Cloud and supports copying objects across
  storage classes and/or locations.

Bug Fixes
---------
- Fixed a bug that could cause downloads to have a hash mismatch (and deletion
  of the corrupted file) when resumed across process breaks via a tracker file.

Other Changes
-------------
- Updated documentation and examples for several topics including
  acl, cp, dev, signurl, stat, and wildcards.


Release 4.11 (release date: 2015-03-10)
=======================================
New Features
------------
- Added Nearline storage class support to the mb command.

Bug Fixes
---------
- Fixed a bug for streaming uploads that could occasionally cause a HTTP 410
  from the service or a hash mismatch (and deletion of the corrutped file).
- Fixed an OverflowError that occurred when uploading files > 4GiB on a 32-bit
  operating system.

Other Changes
-------------
- Added documentation around using the Content-MD5 header to extend integrity
  checking to include checksums computed by a client-side content pipeline.


Release 4.10 (release date: 2015-03-03)
=======================================
Bug Fixes
---------
- Fixed a bug that could cause undetected data corruption (preserving incorrect
  data) if a streaming upload encountered a service error on non-8KiB-aligned
  boundary.
- Fixed a bug that caused downloads to be truncated if the connection broke,
  resulting in a hash mismatch (and deletion of the corrupted file) for that
  download.
- Fixed a format string arguments error that occurred if a download exhausted
  all retries.

Other Changes
-------------
- The lifecycle command now accepts JSON input in the form of
  "{ "lifecycle": { "rule" ..." in addition to "{ "rule": ...".
- Improved access token expiry logic for GCE credentials.


Release 4.9 (release date: 2015-02-13)
=======================================
New Features
------------
- When using the JSON API, the ch acl/defacl subcommand now supports
  project groups via the -p flag. For details, see "gsutil help acl ch".

Bug Fixes
---------
- Fixed a bug that caused daisy-chain copies (including cross-provider
  copies) for files large than 100MiB to fail.
- Fixed a bug that caused streaming uploads than ran for longer than
  an hour to fail with HTTP 400s.
- Fixed a bug where perfdiag would not properly clean up its test files.
- Fixed a bug where using ls with the XML API could mistakenly report bucket
  configuration as present.

Other Changes
-------------
- Updated documentation for metadata, retries, security, and subdirs.
- Tracker files are no longer written for small downloads.


Release 4.8 (release date: 2015-01-23)
=======================================
New Features
------------
- gsutil now supports HTTP proxy configuration via the http_proxy,
  https_proxy, or HTTPS_PROXY environment variables. This configuration
  is used only if proxy configuration is not present in the .boto
  configuration file.
- gsutil rsync now supports regex-based source and destination URL
  exclusion via the -x flag.
- The rm command now supports arguments on stdin via the -I flag.

Bug Fixes
---------
- Fixed a bug where perfdiag would fail if netstat was not available.
- Fixed a bug where temporary ca_certs files were not being cleaned up.
- Fixed a bug in rsync to unnecessarily remove or write objects, in some
  cases leaving the destination in a non-synchronized state.
  caused rsync to unnecessarily remove or rewrite objects.
- Fixed a bug where rsync temporary listing files were not being
  cleaned up when the rsync process was killed.
- Fixed a bug where rsync would remove destination URLs if listing the
  source encountered a non-retryable failure (for example, if the source
  did not exist).
- Fixed a bug where mv would fail for some Unicode filenames.
- Fixed a bug where mv would remove the source URL after skipping the
  destination URL.
- Fixed a bug that caused daisy chain uploads to hang if the download thread
  raised an exception.
- Fixed a bug where acl ch would return a zero exit code even if it failed.
- Fixed a bug that sometimes caused the progress display to render multiple
  times at the end of an upload or download.

Other Changes
-------------
- Resumable uploads of files using the JSON API now send their data in a
  single request, making separate HTTP calls only when resuming is necessary.
- The test command now runs tests in parallel by default, and test
  parallelism on Windows is now supported.
- All non-streaming downloads are now resumable (and retryable) by default,
  regardless of size.
- Canned ACLs and canned default object ACLs are now supported in the JSON
  API (previously they would fall back to using the XML API).
- Google Compute Engine service account credential tokens are now cached,
  avoiding unnecessary refreshes.
- Improved detection of the Google Compute Engine metadata server,
  particularly when using the -m flag for multiprocessing.
- Added new help sections about filename encoding and security/privacy
  considerations.
- Download progress is now displayed for small XML API downloads.


Release 4.7 (release date: 2014-11-17)
=======================================
New Features
------------
- Tab completion now works on gs:// URLs (for Cloud SDK installs only).
  To install via Cloud SDK, see https://cloud.google.com/sdk/#Quick_Start
- Streaming uploads (with source URL "-") using the JSON API now buffer
  in-memory up to 100MB, allowing large streams to be retried in the event
  of network flakiness or service errors.
- Resumable uploads that receive a fatal service error (typically a 410)
  are now automatically retried from the beginning.

Bug Fixes
---------
- Fixed an apitools bug that impacted upload performance and caused
  "Retrying from byte __ after exception" to print after every 100MiB.
- Fixed _$folder$ placeholder object detection on versioned buckets.
- Removed an unnecessary credential check on load which increased
  startup time by over one second in some cases.
- SignURL now properly retries when checking if the signed object is
  readable.
- Files with both Content-Encoding and Content-Type gzip are now properly
  removed when hash validation fails (only one of the two should be set).
- The x-goog-if-generation-match:0 header now works properly with the XML API.
- Fixed a bug that caused "defacl ch" on a bucket with a private ACL to fail.
- The rm command now properly supports precondition headers.
- Fixed a bug that caused large streaming uploads to fail with the message
  "Failure: length too large" when using the JSON API.
- Fixed a bug that caused JSON lifecycle configurations with createdBefore
  conditions to fail with a DecodeError.

Other Changes
-------------
- Byte counts now display accurate abbreviations of binary sizing. For example,
  messages previously labeled MB are now properly labeled MiB to indicate
  2**20 bytes. Only the labeling changed - the actual sizes were always binary.
- Improved Cloud SDK integration, including improved error messages
  and instructions.
- The num_retries .boto configuration value now applies to all requests
  (previously it was ignored for JSON API requests).
- rsync now works with non-existent destination subdirectories.
- Raised the default resumable upload threshold from 2MB to 8MB to
  improve performance.
- Benign retry messages now print only when debug mode is enabled via the
  top-level -d flag.
- The top-level -q flag now suppresses suggestions to use the -m flag.
- Command synopsis is now output when the wrong number of arguments are
  provided.
- Removed dependency on google-api-python-client module, added dependencies on
  oauth2client and six modules.

Release 4.6 (release date: 2014-09-08)
=======================================

Bug Fixes
---------
- Fixed a TypeError bug that occurred in perfdiag write throughput tests.
- Fixed an rsync bug that caused invalid symlinks to abort the transfer
  even when -e option was specified.
- Fixed a perfdiag assumption that ipaddrlist was populated.
- Fixed an AttributeError when setting an invalid canned ACL with defacl set.
- Fixed a bug where non-resumable uploads would include payload in debug output
  when for running in debug mode (-D).

Other Changes
-------------
- Added the proxy_rdns configuration variable for clients that
  do DNS lookups via a proxy.
- Added the state_dir configuration variable for choosing the location of
  gsutil's internal state files, including resumable transfer tracker files.
  resumable_tracker_dir configuration variable is now deprecated.
- Added DNS, connection latency, and proxy use information to perfdiag
  command.
- perfdiag command will not perform DNS lookups if they are disabled in
  boto config.
- perfdiag command will now only attempt to delete uploaded objects when
  running write tests.
- Added code coverage support to test command.
- rsync -d now succeeds on a 404 for a to-be-deleted object (for example, when
  the object was already deleted by an external process).

Release 4.5 (release date: 2014-08-14)
=======================================

Bug Fixes
---------
- Fixed a bug that caused resumable uploads to restart if gsutil was
  terminated with CTRL-C.
- Fixed a bug in defacl ch command that caused a failure when updating
  an existing default object ACL entry.
- Fixed an invalid literal bug during rsync file listing.
- Made several improvements to JSON upload stability, including fixing a bug
  which occasionally caused resumable upload hashes not to catch up properly.
- All JSON calls now have socket timeouts, eliminating hangs under
  flaky network conditions.
- Fixed a bug where acl ch -g AllAuthenticatedUsers would instead add
  AllUsers.
- Fixed a bug that caused object custom metadata not to be preserved when
  copying in the cloud.
- Fixed a bug where du -s did not properly elide subdirectories.

Other Changes
-------------
- Parallel composite uploads are now disabled by default until crcmod is
  available in major Linux distributions. To re-enable the setting from
  prior versions, in the [GSUtil] section of your .boto config file, add:
  parallel_composite_upload_threshold=150M
- Non-wildcarded URLs for existing objects now use Get before trying List
  (as in gsutil3), and thus are not subject to eventual listing consistency.
- gsutil -D now redacts proxy configuration values in the output.

Release 4.4 (release date: 2014-07-17)
=======================================

New Features
------------
- Added the hash command, which can calculate hashes of local files.
  gsutil already calculates hashes for integrity checking, but this allows
  the user to separately calculate the MD5 and CRC32c hashes of a local file.

Bug Fixes
---------
- Many improvements to JSON API media transfers, including far
  more robust retry logic.
- Fixed "File changed during upload: EOF..." errors on XML resumable uploads.
- Fixed rsync command to read and write index files in binary mode.
- Fix potential TypeError in _CheckAndHandleCredentialException.
- Fixed possible data corruption when using JSON API uploads for
  small files with lines starting with "From:", which would cause
  integrity checks to fail.
- Fixed gsutil cp to skip directory placeholders when downloading, avoiding
  "directory exists where the file needs to be created" errors.
- Fixed daisy chain cp/rsync for files >= 100MB.
- Fixed a bug in JSON proxy support where the proxy info was sometimes unused.
- Fixed a bug where an acl get on a private default object ACL returned an
  error instead of a blank ACL.
- Fixed a JSON API issue with large HTTP responses on 32-bit systems.

Other Changes
-------------
- Improved object listing performance when using the XML API.
- Improved various error messages.
- Improved progress display during media transfer.
- Switched to truncated exponential backoff for retries.
- Improved OS-specific ulimit checks.
- Added some information such as OS and Cloud SDK wrapping to gsutil version,
  and changed the output format to be more uniform.
- Daisy chain cp/rsync now supports resumable uploads.
- Improved proxy support for proxy username and passwords.
- x-amz headers are now supported for cp, rsync, and setmeta.  x-amz-meta
  headers continue to be supported as well.

Release 4.3 (release date: 2014-06-10)
=======================================

Bug Fixes
---------
- Fix acl/defacl ch changing the role of an existing group.
- Fix unicode and 404 errors when using manifests.
- Fix parallelism configuration bug that limited gsutil rsync to two threads
  and could lead to rsync hangs. "gsutil -m rsync" runs much faster, and rsync
  uploads of large local files are now faster via parallel composite upload.
  Parallel composite uploads of large files are also faster.
- Fix rsync bug with parallel composite uploads.
- Fix TypeError that could occur when running the cp command with no
  credentials.

Other Changes
-------------
- Progress indicators for -m cp/rsync commands are now more readable.
- Added command being run to gsutil -d/-D output.
- Lowered default parallelism for 'gsutil -m test' and added hang detection.

Release 4.2 (release date: 2014-06-05)
=======================================

New Features
------------
- Added parallel test execution support to test command, ex: "gsutil -m test"

Bug Fixes
---------
- Fix failure during retry of an XML download.
- Moved to boto release 2.29.1 fixing boto authentication erroneously
  reporting OAuth2 credentials as invalid.
- Fix parallel composite uploads when using only a single process and thread.
- Fix an invalid seek during daisy chain operation that affected file copy
  from Google Cloud Storage -> S3 for files greater than 8KB in size.
- Fix "gsutil acl ch" with AllUsers or AllAuthenticatedUsers groups.
- Fix some copy errors writing new lines to the manifest file.
- Fix "gsutil test" return code to properly be 0 on success.

Other Changes
-------------
- "gsutil cp -z" now ignores whitespace in the extension list.

Release 4.1 (release date: 2014-05-28)
=======================================

Bug Fixes
---------
- Fixed a bug in parallel composite uploads where uploads with
  existing components would fail.
- Moved gcs-oauth2-boto-plugin to version 1.5, fixing a bug in the PyPi gsutil
  distribution that would cause gsutil to unnecessarily attempt to query
  the Google Compute Engine metadata service.

Other Changes
-------------
- Parallel composite uploads no longer specify an if-not-match precondition
  when uploading component parts.
- Parallel composite uploads no longer calculate a CRC32c hash prior to
  uploading component parts (these are still validated by an MD5 hash).
- Removed apitools dependency on gflags.

Release 4.0 (release date: 2014-05-27)
=======================================

Major New Gsutil Version - Backwards-Incompatible Changes
------------------------------
- The Google Cloud Storage configuration data supported by the acl, cors,
  and lifecycle commands now uses the JSON format instead of the older XML
  format. gsutil 4.0 will fail and provide conversion instructions if an XML
  configuration file is provided as an argument for a gs:// URL.
- gsutil no longer accepts arbitrary headers via the global -h flag.
  Documented headers for gsutil commands are still supported; for the
  full list of supported headers, see "gsutil help command_opts".
- The compose command will now default the destination object's
  Content-Type to the Content-Type of the first source object if none
  is provided via the -h global flag.
- The long-deprecated -t and -q options have been removed from the cp command.
- The perfdiag command no longer supports adding a host header.
- Having OAuth2 User Account credentials and OAuth2 Service Account
  credentials configured simultaneously will now fail with an error message
  to avoid confusion.  Also, a single invalid credential will fail with an
  error message.  See "gsutil help creds" for details.
- Bucket relocate scripts have been removed.
- Downloading object names ending with '/' is no longer supported to avoid
  problems this caused for directores using the Google Cloud Console.
- rm -r now implies rm -ra (removing all object versions recursively).
- All commands using the global -m option or a force option (such as
  rm -f or cp -c) will now return a non-zero exit code if there are any
  failures during the operation.
- MD5 and CRC32c values are now represented in base64 encoding instead
  of hex encoding (this includes manifest files).

New Features
------------
- The Google Cloud Storage JSON API (v1) is now the default API used
  by gsutil for all commands targeting gs:// URLs. The JSON API is more
  bandwidth efficient than the older XML API when transferring metadata
  and does not require separate calls to preserve object ACLs when copying.
  The XML API will automatically be used when accessing s3:// URLs.
- The Google Cloud Storage XML API can be used in lieu of the JSON API
  by setting 'prefer_api = xml' in the GSUtil section of your boto config file.
- Added the rsync command that can synchronize cloud and local directories.
- Added the signurl command that can generate Google Cloud Storage signed URLs.
- The perfdiag command now supports a listing latency test.
- The rb command now supports a -f flag allowing it to continue when errors
  are encountered.
- The test command now supports a -s flag that runs tests against S3.

Other Changes
-------------
- All python files not under a third_party directory are now pylint-clean,
  with the exception of TODO-format and a handful of warnings in root-level
  files. As part of the de-linting process, many edge-case bugs were
  identified and fixed.
- The ls command now operates depth-first (as in Unix ls) instead
  of breadth-first.
- Daisy-chain copying does not currently support resumable uploads.
- Several compatibility improvements for Windows and S3.


Release 3.42 (release-date: 2014-01-15)
=======================================

Other Changes
-------------

- Fixed potential bug with update command on CentOS.


Release 3.41 (release-date: 2014-01-14)
=======================================

Other Changes
-------------

- Changes to protect security of resumable upload IDs.


Release 3.40: Skipped


Release 3.39: Skipped


Release 3.38 (release-date: 2013-11-25)

Bug Fixes
---------

- Fix to include version number in user-agent string.
- Fix bug wherein -m flag or parallel uploads caused crash on systems without
  /dev/shm.
- Fix SSL errors and invalid results with perfdiag -c and -k rthru test.
- Fixed cases where parallel composite uploads could leave orphaned components.
- Fix bug attempting to stat objects you don't have auth to read.
- Fixed bug breaking defacl's -d option.


Other Changes
-------------

- Fixed gsutil config doc.
- Fixed references to old command names; fix defacl ch example.
- Improved error messages for deprecated command aliases.
- Updated gsutil support info.


New Features
------------

- Enabled -R flag for recursion with setmeta command.


Release 3.37 (release-date: 2013-09-25)
=======================================

Bug Fixes
---------

- Fix parsing of -R for "acl ch" and chacl commands.
- Fixed import statement of unittest2 which caused installations using Python
  2.6 without unittest2 installed to fail when starting up gsutil.


Other Changes
-------------

- Fixed tests so they pass on Windows and package installs.
- Add a root logging handler manually instead of relying on basicConfig.
- Fix apiclient import statement.
- Exponential backoff for access token requests.
- Fix flakiness in test TearDown to account for eventual consistency of object
  listings.


Release 3.36 (release-date: 2013-09-18)
=======================================

Bug Fixes
---------

- Fix bug when a 400 or 403 exception has no detail.
- Fix bugs with config -e and config -o.


Other Changes
-------------

- Clarify stat command documentation regarding trailing slashes.
- Add Generation and Metageneration to gsutil stat output.


New Features
------------

- Set config values from command line with -o.


Release 3.35 (release-date: 2013-09-09)
=======================================

Bug Fixes
---------

- Fix streaming upload to S3 and provide more useful stack traces multi-threaded failures.
- Fix race condition in test_rm.
- Fix retry decorator during test bucket cleanup.
- Fixed cat bug that caused version to be ignored in URIs.
- Don't decode -p or -h values other than x-goog-meta-. Fixes ability to use string project names.
- Update bucket_relocate.sh to work on GCE.
- Fix recursive uploading from subdirectories with unexpanded wildcard as source URI.
- Make gsutil error text include <Message> content.
- Change shebang line back to python because this doesn't work on some systems.
- Fix hash_algs differences in perfdiag.
- Update Python version check and shebang line.
- Enforce project_id entry in config command; provide friendly error if missing proj ID.
- Use transcoding-invariant headers when available in gs.Key.
- Make gsutil cp not fail if unable to check versioning config on dest bucket.
- Make gsutil detect when config fails because of proxy and prompt for proxy config.
- Avoid checking metageneration attribute when long-listing S3 objects.
- Exclude the no-op auth handler as indicating credentials are configured.


New Features
------------

- Implemented gsutil stat command.


Other Changes
-------------

- Consolidate config-related commands.
- Changed rm -r gs://bucket to delete bucket at end.
- Various doc cleanup and improvement.
- Warn user before updating to major new version. Also fixed minor version comparison bug, and added tests.
- Change max component count to 1024.
- Add retry-decorator as a submodule.
- Explicitly state control chars to avoid in gsutil naming documentation.
- Make config command recommend project strings.
- Made long listing format a little better looking.
- Allow --help flag for subcommands.
- Implement help for subcommands and add OPTIONS sections for subcommands.
- Add more detailed error message to notification watchbucket command.
- Add notification URL configuration for notification tests.
- Refactor to use upstream retry_decorator as external dependency.
- Distribute cacerts file with gsutil.
- Updated gsutil help to point to Google Cloud Console instead of older APIs console.
- Make gsutil pass bundled cacerts.txt to oauth2client; stop checking SHA1 of certs, now that we no longer depend on boto distribution.
- Move all TTY checks to a common util function and mock it for update tests.
- Fix duplicate entry created in .gitmodules.
- Fix unit test breakage because VERSION file is old.
- Fix test using ? glob with ObjectToURI.
- Fix update tests that fail for package installs.
- Change bucket delete teardown to try more times.
- Fix tests that perform operations on bucket listings.
- Keep package install set to True unless VERSION file doesn't exist.
- Fix handling of non-numeric version strings in update test.


Release 3.34 (release-date: 2013-07-18)
=======================================

Bug Fixes
---------

- Fixed a bug where the no-op authentication handler was being loaded after
  other authentication plugins, causing the no-op handler to be chosen instead
  of other valid credentials.


Release 3.33 (release-date: 2013-07-16)
=======================================

Bug Fixes
---------

- Added .git* to MANIFEST.in excludes and fixed cp doc typo. This was needed to
  overcome problem caused by accidental inclusion of .git* files in release,
  which caused the update command no longer to allow updates (since starting
  in 3.32 it checks whether the user has any extraneous files in the gsutil
  directory before updating)


Release 3.32 (release-date: 2013-07-16)
=======================================

New Features
------------

- Added support for getting and setting lifecycle configuration for buckets.
- Implemented Parallel Composite Uploads.
- Added a new du command that displays object size, similar to Linux du.


Bug Fixes
---------

- Fixed a bug when using ls -R on objects with trailing slashes. Closes #93.
- Fixed so won't crash in perfdiag when nslookup is missing or gethostbyname
  fails.
- Smartly compare version strings during autoupdate check.
- Made header handling for upload case-insensitive.
- Re-enabled software update check for users with no credentials configured.
- Fixed incorrectly-generated password editing comment in service account
  config. Fixes #146.


Other Changes
-------------

- Improved flow when encounter auth failure for GCE service account with no
  configured storage scopes:
    1. Changed HasConfiguredCredentials() logic not to include
       has_auth_plugins as part of the evaluated expression, since that will
       always evaluate to true under GCE (since GCE configures its internal
       service account plugin under /etc/boto.cfg).
    2. Changed ConfigureNoOpAuthIfNeeded logic so we configure no-op auth
       plugin even if there is a config_file list, since GCE always configures
       /etc/boto.cfg, even if user has no storage scopes configured.
    3. Additional changes:
      a. Removed assertion of oauth access token cache check log from
         test_Doption.py, which may not be true sometimes (e.g., if user is
         using HMAC creds).
      b. Removed remnants of CONFIG_REQUIRED left over from earlier CL.
      c. Merged dupe _ConfigureNoOpAuthIfNeeded functions from two code files,
         moved to util.py.
- Fixed confusing gsutil rm "Omitting" message.
- Wrapped long gsutil update message.
- Silenced additional possible perfdiag errors.
- Improved perfdiag performance by only generating one chunk of random file.
- Changed to swallow broken pipe errors when piping gsutil to other programs.
- Made DotfulBucketNameNotUnderTld error message more user friendly.
- Extracted function for building ACL error text from main try/except loop,
  for better readability.
- Disallowed gsutil update when user data present in gsutil dir.
- Plumbed accept-encoding into HEAD requests in ls -L command.
- Updated README and moved ReleaseNotes.txt to CHANGES.md.
- Updated crcmod docs with link to Windows installer.
- Updated documentation regarding gzip content-encoding.
- Removed StorageUri parse check for lone ':' (interferes with using filenames
  containing ':')
- Added tests for gsutil update check and fixed bug for bad file contents.
- Set accept-encoding and handle gzip on-the-fly encoding.


Release 3.31 (release-date: 2013-06-10)
=======================================

New Features
------------

- Implemented consumption of manifest files for cp.
- Add ETag to ls -l and make ls -b variants more efficient.
- Expand the manifest path to allow for tildes in paths.
- Added bucket_relocate.sh script to gsutil.


Bug Fixes
---------

- Fix gsutil cp -R to copy all versioned objects.
- Fixed bug where gsutil cp -D -n caused precondition failure.
- Fixed gsutil daisy-chain copy to allow preserving ACLs when copying within
  same provider.
- Fix identification of non-MD5 ETags.
- Fixed bugs where gsutil -q cp and gsutil cp -q sometimes weren't quiet.
- Fixed unicode error when constructing tracker filename from non-ASCII
  Unicode filename.
- Fixed that noclobber would not resume partial resumable downloads.
- Fixed bug when running gsutil cp -Dp by user other than object owner.
- Properly encode metageneration and etag in ls output with -a and -e.
- Update resumable threshold stated in gsutil help prod.


Other Changes
-------------

- ls -Lb no longer shows total # files/total size of bucket, so that ls -Lb
  instead provides an efficient way to view just the metadata for large buckets.
- Catch and ignore EEXIST error when creating gsutil tracker dir.
- Add note to gsutil update doc about auto-update checks being disabled with
  gsutil -q option.
- Disable hashing and increase buffer size in perfdiag.
- Added better error messages for service account auth.
- Make perfdiag behave more like normal gsutil, with multi-threading option.
- Changed so auto-update check/prompt aren't made if gsutil -q specified.
- Changed gsutil mb command to clarify that EU means European Union.
- Added doc warnings about losing version ordering if using gsutil -m cp
  between versioned buckets; removed trailing whitespace.
- Added to gsutil cp -L doc to describe how to build a reliable script for
  copying many objects.


Release 3.30 (release-date: 2013-06-10)
=======================================

- Abandoned.


Release 3.29 (release-date: 2013-05-13)
=======================================

Bug Fixes
---------

- Fixed incorrect package installation detection that resulted in not being
  able to run the update command while running gsutil from a symlink.

Other Changes
-------------

- Added a test for debug mode (gsutil -D) output.
- List numbering and title case fixes in additional help pages.
- Removed dateutil module dependency from cp command test.
- Updated documentation to clarify that public-read objects are cached for 1
  hour by default.
- Added a filter to suppress "module was already imported" warnings that were
  sometimes printed while running gsutil on Google Compute Engine instances.


Release 3.28 (release-date: 2013-05-07)
=======================================

New Features
------------

- Added support for new Object Change Notifications feature.

Bug Fixes
---------

- Fixed problem where gsutil update command didn’t take default action.
- Fixed a problem with the update command sometimes triggering an additional
  update command.

Other Changes
-------------

- Add packaging information to version output.
- Removed fancy_urllib, since it is no longer used.
- Changed num_retries default for resumable downloads to 6.
- Don’t check for newer software version if gs_host is specified in boto
  config file.
- Modified oauth2client logging behavior to be consistent with gsutil.
- Added gs_port configuration option.
- Skip update tests when SSL is disabled.


Release 3.27 (release-date: 2013-04-25)
=======================================

New Features
------------

- Added a human readable option (-h) to ls command.
- Changed WildcardIterator not to materialize list of all matching files from
  directory listing (so works faster when walking over large directories)
- Added -f option to setacl command to allow command to continue after errors
  encountered.
- Add manifest log support for the cp command.
- Added never option for check_hashes_config; fixed bug that assumes an ETag
  is always returned from server.
- Made gsutil provide friendlier error message if attempting non-public data
  access with missing credentials.
- Set 70 second default socket timeout for httplib.
- Add ability to run a single test class or function with the test command.

Bug Fixes
---------

- Don't check for updates if the user has no credentials configured. This
  fixes a bug for users without credentials trying to use gsutil for first
  time.
- Fixed case where chacl command incorrectly recognized an email address as a
  domain.
- Fix setmeta command for S3 objects.
- Fixed bug where wildcarded dest URI attempted string op on Key object.
- Fixed case where gsutil -q outputted progress output when doing a streaming
  upload.
- Error handling for out of space during downloads.
- Include ISO 8601-required "Z" at end of timestamp string for gsutil ls -l,
  to be spec-compliant.
- Removed deprecated setmeta syntax and fixed unicode issues.
- Changed update command not to suggest running sudo if running under Cygwin.
- Removed references to deprecated gs-discussion forum from gsutil built-in
  help.
- Add literal quotes around CORS config example URL in gsutil setcors help to
  avoid having example URL turn into an HREF in auto-generated doc.

Other Changes
-------------

- Added proper setup.py to make gsutil installable via PyPi.
- Added warning to gsutil built-in help that delete operations cannot be
  undone.
- Replaced gsutil's OAuth2 client implementation with oauth2client.
- Updates to perfdiag.
- Updated config help about currently supported settings.
- Fixes to setup.py and modified version command.
- Move gslib/commands/cred_types.py to gslib, so only Command subclasses live
  in gslib/commands.
- Updated gsutil setmeta help no longer to warn that setmeta with versioning
  enabled creates a new object.


Release 3.26 (release-date: 2013-03-25)
=======================================

New Features
------------

- Added support for object composition.
- Added support for external service accounts.
- Changed gsutil to check for available updates periodically (only while
  stdin, stderr, stdout are connected to a TTY, so as not to interfere with
  cron jobs).
- Added chdefacl command.
- Made gsutil built-in help available under
  https://developers.google.com/storage/docs/gsutil
- Add a command suggestion when the command name is not found.
- Added byte suffix parsing to the -s parameter of perfdiag.
- Added --help support to subcommands. Fixes #96.
- Updated perfdiag command to track availability and record TCP settings.
- Added metadata parameter to perfdiag command.
- Added support for specifying byte range to cat command.
- Output more bucket metadata on ls -Lb.
- Implemented gsutil -q (global quiet) option (fixes issue #130). Also changed
  gsutil to output all progress indicators using logging levels. Also changed
  help command not to output bold escape sequences and not use PAGER if stdout
  is not a tty, which also fixes bug that caused gsutil help test to fail.
- Plumbed https_validate_certificates through to OAuth2 plugin handler,
  allowing control over cert validation for OAuth2 requests
- Fixed ISO 639.1 ref in config command help text

Bug Fixes
---------

- Fixed bug where gsutil cp -D didn't preserve metadata
- Fixed problem where gsutil -m is hard to interrupt (partial fix for issue
  #99 - only for Linux/MacOS; problem still exists for Windows).
- Fixed broken reference to boto_lib_dir in update command.
- Made changing ACL not retry on 400 error.
- Fixed name expansion bug for case where uri_strs is itself an iterator
  (issue #131); implemented additional naming unit test for this case.
- Fixed flaky gsutil rm test
- Fixed a bug in the chacl command that made it so you couldn't delete the
  AllAuthenticatedUsers group from an ACL.

Other Changes
-------------

- Refactored gsutil main function into gslib, with gsutil being a thin
  wrapper.
- Added a test for the update command.
- Renamed gsutil meta_generation params to metageneration, for consistency
  with GCS docs.
- Removed .pyc files from tarball/zipfile.
- Added new root certs to cacerts.txt, to provide additional flexibility
  in the future.


Release 3.25 (release-date: 2013-02-21)
=======================================

Bug Fixes
---------

- Fixed two version-specific URI bugs:
    1. gsutil cp -r gs://bucket1 gs://bucket2 would create objects in bucket2
       with names corresponding to version-specific URIs in bucket1 (e.g.,
       gs://bucket2/obj#1361417568482000, where the "#1361417568482000" part was
       part of the object name, not the object's generation).

       This problem similarly caused gsutil cp -r gs://bucket1 ./dir to create
       files names corresponding to version-specific URIs in bucket1.
    2. gsutil rm -a gs://bucket/obj would attempt to delete the same object
       twice, getting a NoSuchKey error on the second attempt.


Release 3.24 (release-date: 2013-02-19)
=======================================

Bug Fixes
---------

- Fixed bug that caused attempt to dupe-encode a unicode filename.

Other Changes
-------------

- Refactored retry logic from setmeta and chacl to use @Retry decorator.
- Moved @Retry decorator to third_party.
- Fixed flaky tests.


Release 3.23 (release-date: 2013-02-16)
=======================================

Bug Fixes
---------

- Make version-specific URI parsing more robust. This fixes a bug where
  listing buckets in certain cases would result in the error
  'BucketStorageUri' object has no attribute 'version_specific_uri'


Release 3.22 (release-date: 2013-02-15)
=======================================

New Features
------------

- Implemented new chacl command, which makes it easy to add and remove bucket
  and object ACL grants without having to edit XML (like the older setacl
  command).
- Implemented new "daisy-chain" copying mode, which allows cross-provider
  copies to run without buffering to local disk, and to use resumable uploads.
  This copying mode also allows copying between locations and between storage
  classes, using the new gsutil cp -D option. (Daisy-chain copying is the
  default when copying between providers, but must be explicitly requested for
  the other cases to keep costs and performance expectations clear.)
- Implemented new perfdiag command to run a diagnostic test against
  a bucket, collect system information, and report results. Useful
  when working with Google Cloud Storage team to resolve questions
  about performance.
- Added SIGQUIT (^\) handler, to allow breakpointing a running gsutil.

Bug Fixes
---------

- Fixed bug where gsutil setwebcfg signature didn't match with
  HMAC authentication.
- Fixed ASCII codec decode error when constructing tracker filename
  from non-7bit ASCII input filename.
- Changed boto auth plugin framework to allow multiple plugins
  supporting requested capability, which fixes gsutil exception
  that used to happen where a GCE user had a service account
  configured and then ran gsutil config.
- Changed Command.Apply method to be resilient to name expansion
  exceptions. Before this change, if an exception was raised
  during iteration of NameExpansionResult, the parent process
  would immediately stop execution, causing the
  _EOF_NAME_EXPANSION_RESULT to never be sent to child processes.
  This resulted in the process hanging forever.
- Fixed various bugs for gsutil running on Windows:
  - Fixed various places from a hard-coded '/' to os.sep.
  - Fixed a bug in the cp command where it was using the destination
    URI's .delim property instead of the source URI.
  - Fixed a bug in the cp command's _SrcDstSame function by
    simplifying it to use os.path.normpath.
  - Fixed windows bug in tests/util.py _NormalizeURI function.
  - Fixed ZeroDivisionError sometimes happening during unit tests
    on Windows.

- Fixed gsutil rm bug that caused exit status 1 when encountered
  non-existent URI.
- Fixed support for gsutil cp file -.
- Added preconditions and retry logic to setmeta command, to
  enforce concurrency control.
- Fixed bug in copying subdirs to subdirs.
- Fixed cases where boto debug_level caused too much or too little
  logging:
  - resumable and one-shot uploads weren't showing response headers
    when connection.debug > 0.
  - payload was showing up in debug output when connection.debug
    < 4 for streaming uploads.

- Removed XML parsing from setacl. The previous implementation
  relied on loose XML handling, which could truncate what it sends
  to the service, allowing invalid XML to be specified by the
  user. Instead now the ACL XML is passed verbatim and we rely
  on server-side schema enforcement.
- Added user-agent header to resumable uploads.
- Fixed reporting bits/s when it was really bytes/s.
- Changed so we now pass headers with API version & project ID
  to create_bucket().
- Made "gsutil rm -r gs://bucket/folder" remove xyz_$folder$ object
  (which is created by various GUI tools).
- Fixed bug where gsutil binary was shipped with protection 750
  instead of 755.

Other Changes
-------------

- Reworked versioned object handling:
  - Removed need for commands to specify -v option to parse
    versions. Versioned URIs are now uniformly handled by all
    commands.
  - Refactored StorageUri parsing that had been split across
    storage_uri and convenience; made versioned URIs render with
    version string so StorageUri is round-trippable (boto change).
  - Implemented gsutil cp -v option for printing the version-specific
    URI that was just created.
  - Added error detail for attempt to delete non-empty versioned
    bucket. Also added versioning state to ls -L -b gs://bucket
    output.
  - Changed URI parsing to use pre-compiled regex's.
  - Other bug fixes.

- Rewrote/deepened/improved various parts of built-in help:
  - Updated 'gsutil help dev'.
  - Fixed help command handling when terminal does not have the
    number of rows set.
  - Rewrote versioning help.
  - Added gsutil help text for common 403 AccountProblem error.
  - Added text to 'gsutil help dev' about legal agreement needed
    with code submissions.
  - Fixed various other typos.
  - Updated doc for cp command regarding metadata not being
    preserved when copying between providers.
  - Fixed gsutil ls command documentation typo for the -L option.
  - Added HTTP scheme to doc/examples for gsutil setcors command.
  - Changed minimum version in documentation from 2.5 to 2.6 since
    gsutil no longer works in Python 2.5.
  - Cleaned up/clarify/deepen various other parts of gsutil
    built-in documentation.

- Numerous improvements to testing infrastructure:
  - Completely refactored infrastructure, allowing deeper testing
    and more readable test code, and enabling better debugging
    output when tests fail.
  - Moved gslib/test_*.py unit tests to gslib/tests module.
  - Made all tests (unit and integration, per-command and modules
    (like naming) run from single gsutil test command.
  - Moved TempDir functions from GsUtilIntegrationTestCase to
    GsUtilTestCase.
  - Made test runner message show the test function being run.
  - Added file path support to ObjectToURI function.
  - Disabled the test command if running on Python 2.6 and unittest2
    is not available instead of breaking all of gsutil.
  - Changed to pass GCS V2 API and project_id from boto config
    if necessary in integration_testcase#CreateBucket().
  - Fixed unit tests by using a GS-specific mocking class to
    override the S3 provider.
  - Added friendlier error message if test path munging fails.
  - Fixed bug where gsutil test only cleaned up first few test files.
  - Implemented setacl integration tests.
  - Implemented StorageUri parsing unit tests.
  - Implemented test for gsutil cp -D.
  - Implemented setacl integration tests.
  - Implemented tests for reading and seeking past end of file.
  - Implemented and tests for it in new tests module.
  - Changed cp tests that don't specify a Content-Type to check
    for new binary/octet-stream default instead of server-detected
    mime type.

- Changed gsutil mv to allow moving local files/dirs to the cloud.
  Previously this was disallowed in the belief we should be
  conservative about deleting data from local disk but there are
  legitimate use cases for moving data from a local dir to the
  cloud, it's clear to the user this would remove data from the
  local disk, and allowing it makes the tool behavior more
  consistent with what users would expect.
- Changed gsutil update command to insist on is_secure and
  https_validate_certificates.
- Fixed release no longer to include extraneous boto dirs in
  top-level of gsutil distribution (like bin/ and docs/).
- Changed resumable upload threshold from 1 MB to 2 MB.
- Removed leftover cloudauth and cloudreader dirs. Sample code
  now lives at https://github.com/GoogleCloudPlatform.
- Updated copyright notice on code files.


Release 3.21 (release-date: 2012-12-10)
=======================================

New Features
------------

- Added the ability for the cp command to continue even if there is an
  error. This can be activated with the -c flag.
- Added support for specifying src args for gsutil cp on stdin (-I option)

Bug Fixes
---------

- Fixed gsutil test cp, which assumed it was run from gsutil install dir.
- Mods so we send generation subresource only when user requested
  version parsing (-v option for cp and cat commands).

Other Changes
-------------

- Updated docs about using setmeta with versioning enabled.
- Changed GCS endpoint in boto to storage.googleapis.com.


Release 3.20 (release-date: 2012-11-30)
=======================================

New Features
------------

- Added a noclobber (-n) setting for the cp command. Existing objects/files
  will not be overwritten when using this setting.

Bug Fixes
---------

- Fixed off-by-one error when reporting bytes transferred.

Other Changes
-------------

- Improved versioning support for the remove command.
- Improved test runner support.


Release 3.19 (release-date: 2012-11-26)
=======================================

New Features
------------

- Added support for object versions.
- Added support for storage classes (including Durable Reduced Availability).

Bug Fixes
---------
- Fixed problem where cp -q prevented resumable uploads from being performed.
- Made setwebcfg and setcors tests robust wrt XML formatting variation.

Other Changes
-------------

- Incorporated vapier@ mods to make version command not fail if CHECKSUM file
  missing.
- Refactored gsutil such that most functionality exists in boto.
- Updated gsutil help dev instructions for how to check out source.


Release 3.18 (release-date: 2012-09-19)
=======================================

Bug Fixes
---------

- Fixed resumable upload boundary condition when handling POST request
  when server already has complete file, which resulted in an infinite
  loop that consumed 100% of the CPU.
- Fixed one more place that outputted progress info when gsutil cp -q
  specified (during streaming uploads).

Other Changes
-------------

- Updated help text for "gsutil help setmeta" and "gsutil help metadata", to
  clarify and deepen parts of the documentation.


Release 3.17 (release-date: 2012-08-17)
=======================================

Bug Fixes
---------

- Fixed race condition when multiple threads attempt to get an OAuth2 refresh
  token concurrently.

Other Changes
-------------

- Implemented simplified syntax for setmeta command. The old syntax still
  works but is now deprecated.
- Added help to gsutil cp -z option, to describe how to change where temp
  files are written.


Release 3.16 (release-date: 2012-08-13)
=======================================

Bug Fixes
---------

- Added info to built-in help for setmeta command, to explain the syntax
  needed when running from Windows.


Release 3.15 (release-date: 2012-08-12)
=======================================

New Features
------------

- Implemented gsutil setmeta command.
- Made gsutil understand bucket subdir conventions used by various tools
  (like GCS Manager and CloudBerry) so if you cp or mv to a subdir you
  created with one of those tools it will work as expected.
- Added support for Windows drive letter-prefaced paths when using Storage
  URIs.

Bug Fixes
---------

- Fixed performance bug when downloading a large object with Content-
  Encoding:gzip, where decompression attempted to load the entire object
  in memory. Also added "Uncompressing" log output if file is larger than
  50M, to make it clear the download hasn't stalled.
- Fixed naming bug when performing gsutil mv from a bucket subdir to
  and existing bucket subdir.
- Fixed bug that caused cross-provider copies into Google Cloud Storage to
  fail.
- Made change needed to make resumable transfer progress messages not print
  when running gsutil cp -q.
- Fixed copy/paste error in config file documentation for
  https_validate_certificates option.
- Various typo fixes.

Other Changes
-------------

- Changed gsutil to unset http_proxy environment variable if it's set,
  because it confuses boto. (Proxies should instead be configured via the
  boto config file.)


Release 3.14 (release-date: 2012-07-28)
=======================================

New Features
------------

- Added cp -q option, to support quiet operation from cron jobs.
- Made config command restore backed up file if there was a failure or user
  hits ^C.

Bug Fixes
---------

- Fixed bug where gsutil cp -R from a source directory didn't generate
  correct destination path.
- Fixed file handle leak in gsutil cp -z
- Fixed bug that caused cp -a option not to work when copying in the cloud.
- Fixed bug that caused '/-' to be appended to object name for streaming
  uploads.
- Revert incorrect line I changed in previous CL, that attempted to
  get fp from src_key object. The real fix that's needed is described in
  https://github.com/GoogleCloudPlatform/gsutil/issues/72.

Other Changes
-------------

- Changed logging to print "Copying..." and Content-Type on same line;
  refactored content type and log handling.


Release 3.13 (release-date: 2012-07-19)
=======================================

Bug Fixes
---------

- Included the fix to make 'gsutil config' honor BOTO_CONFIG environment
  variable (which was intended to be included in Release 3.12)


Release 3.11 (release-date: 2012-06-28)
=======================================

New Features
------------

- Added support for configuring website buckets.

Bug Fixes
---------

- Fixed bug that caused simultaneous resumable downloads of the same source
  object to use the same tracker file.
- Changed language code spec pointer from Wikipedia to loc.gov (for
  Content-Language header).


Release 3.10 (release-date: 2012-06-19)
=======================================

New Features
------------

- Added support for setting and listing Content-Language header.

Bug Fixes
---------

- Fixed bug that caused getacl/setacl commands to get a character encoding
  exception when ACL content contained content not representable in ISO-8859-1
  character set.
- Fixed gsutil update not to fail under Windows exclusive file locking.
- Fixed gsutil ls -L to continue past 403 errors.
- Updated gsutil tests and also help dev with instructions on how to run
  boto tests, based on recent test refactoring done to in boto library.
- Cleaned up parts of cp help text.


Release 3.9 (release-date: 2012-05-24)
======================================

Bug Fixes
---------

- Fixed bug that caused extra "file:/" to be included in pathnames with
  doing gsutil cp -R on Windows.


Release 3.8 (release-date: 2012-05-20)
======================================

Bug Fixes
---------

- Fixed problem with non-ASCII filename characters not setting encoding before
  attempting to hash for generating resumable transfer filename.


Release 3.7 (release-date: 2012-05-11)
======================================

Bug Fixes
---------

- Fixed handling of HTTPS tunneling through a proxy.


Release 3.6 (release-date: 2012-05-09)
======================================

Bug Fixes
---------

- Fixed bug that caused wildcards spanning directories not to work.
- Fixed bug that gsutil cp -z not to find available tmp space correctly
  under Windows.


Release 3.5 (release-date: 2012-04-30)
======================================

Performance Improvement
-----------------------

- Change by Evan Worley to calculate MD5s incrementally during uploads and
  downloads. This reduces overall transfer time substantially for large
  objects.

Bug Fixes
---------

- Fixed bug where uploading and moving multiple files to a bucket subdirectory
  didn't work as intended.
  (https://github.com/GoogleCloudPlatform/gsutil/issues/92).
- Fixed bug where gsutil cp -r sourcedir didn't copy to specified subdir
  if there is only one file in sourcedir.
- Fixed bug where tracker file included a timestamp that caused it not to
  be recognized across sessions.
- Fixed bug where gs://bucket/*/dir wildcard matches too many objects.
- Fixed documentation errors in help associated with ACLs and projects.
- Changed GCS ACL parsing to be case-insensitive.
- Changed ls to print error and exit with non-0 status when wildcard matches
  nothing, to be more consistent with UNIX shell behavior.


Release 3.4 (release-date: 2012-04-06)
======================================

Bug Fixes
---------

- Fixed problem where resumable uploads/downloads of objects with very long
  names would generate tracking files with names that exceeded local file
  system limits, making it impossible to complete resumable transfers for
  those objects. Solution was to build the tracking file name from a fixed
  prefix, SHA1 hash of the long filename, epoch timestamp and last 16
  chars of the long filename, which is guarantee to be a predictable and
  reasonable length.
- Fixed minor bug in output from 'gsutil help dev' which advised executing
  an inconsequential test script (test_util.py).


Release 3.3 (release-date: 2012-04-03)
======================================

Bug Fixes
---------

- Fixed problem where gsutil ver and debug flags crashed when used
  with newly generated boto config files.
- Fixed gsutil bug in windows path handling, and make checksumming work
  across platforms.
- Fixed enablelogging to translate -b URI param to plain bucket name in REST
  API request.


Release 3.2 (release-date: 2012-03-30)
======================================

Bug Fixes
---------

- Fixed problem where gsutil didn't convert between OS-specific directory
  separators when copying individually-named files (issue 87).
- Fixed problem where gsutil ls -R didn't work right if there was a key
  with a leading path (like /foo/bar/baz)


Release 3.1 (release-date: 2012-03-20)
======================================

Bug Fixes
---------

- Removed erroneous setting of Content-Encoding when a gzip file is uploaded
  (vs running gsutil cp -z, when Content-Encoding should be set). This
  error caused users to get gsutil.tar.gz file uncompressed by the user
  agent (like wget) while downloading, making the file appear to be of the
  wrong size/content.
- Fixed handling of gsutil help for Windows (previous code depended on
  termios and fcntl libs, which are Linux/MacOS-specific).


Release 3.0 (release-date: 2012-03-20)
======================================

Important Notes
---------------

- Backwards-incompatible wildcard change:
  The '*' wildcard now only matches objects within a bucket directory. If
  you have scripts that depend on being able to match spanning multiple
  directories you need to use '**' instead. For example, the command:

        gsutil cp gs://bucket/*.txt

  will now only match .txt files in the top-level directory.

        gsutil cp gs://bucket/**.txt

  will match across all directories.
- gsutil ls now lists one directory at a time. If you want to list all objects
  in a bucket, you can use:

        gsutil ls gs://bucket/**

  or:

        gsutil ls -R gs://bucket

New Features
------------

- Built-in help for all commands and many additional topics. Try
  "gsutil help" for a list of available commands and topics.
- A new hierarchical file tree abstraction layer, which makes the flat bucket
  name space look like a hierarchical file tree. This makes several things
  possible:
  - copying data to/from bucket sub-directories (see “gsutil help cp”).
  - distributing large uploads/downloads across many machines
    (see “gsutil help cp”)
  - renaming bucket sub-directories (see “gsutil help mv”).
  - listing individual bucket sub-directories and for listing directories
    recursively (see “gsutil help ls”).
  - setting ACLs for objects in a sub-directory (see “gsutil help setacl”).

- Support for per-directory (*) and recursive (**) wildcards. Essentially,
  ** works the way * did in previous gsutil releases, and * now behaves
  consistently with how it works in command interpreters (like bash). The
  ability to specify directory-only wildcards also enables a number of use
  cases, such as distributing large uploads/downloads by wildcarded name. See
  "gsutil help wildcards" for details.
- Support for Cross-Origin Resource Sharing (CORS) configuration. See "gsutil
  help cors" for details.
- Support for multi-threading and recursive operation for setacl command
  (see “gsutil help setacl”).
- Ability to use the UNIX 'file' command to do content type recognition as
  an alternative to filename extensions.
- Introduction of new end-to-end test suite.
- The gsutil version command now computes a checksum of the code, to detect
  corruption and local modification when assisting with technical support.
- The gsutil update command is no longer beta/experimental, and now also
  supports updating from named URIs (for early/test releases).
- Changed gsutil ls -L to also print Content-Disposition header.

Bug Fixes
---------

- The gsutil cp -t option previously didn't work as documented, and instead
  Content-Type was always detected based on filename extension. Content-Type
  detection is now the default, the -t option is deprecated (to be removed in
  the future), and specifying a -h Content-Type header now correctly overrides
  the filename extension based handling. For details see "gsutil help
  metadata".
- Fixed bug that caused multi-threaded mv command not to percolate failures
  during the cp phase to the rm phase, which could under some circumstances
  cause data that was not copied to be deleted.
- Fixed bug that caused gsutil to use GET for ls -L requests. It now uses HEAD
  for ls -L requests, which is more efficient and faster.
- Fixed bug that caused gsutil not to preserve metadata during
  copy-in-the-cloud.
- Fixed bug that prevented setacl command from allowing DisplayName's in ACLs.
- Fixed bug that caused gsutil/boto to suppress consecutive slashes in path
  names.
- Fixed spec-non-compliant URI construction for resumable uploads.
- Fixed bug that caused rm -f not to work.
- Fixed UnicodeEncodeError that happened when redirecting gsutil ls output
  to a file with non-ASCII object names.

Other Changes
-------------

- UserAgent sent in HTTP requests now includes gsutil version number and OS
  name.
- Starting with this release users are able to get individual named releases
  from version-named objects: gs://pub/gsutil_<version>.tar.gz
  and gs://pub/gsutil_<version>.zip. The version-less counterparts
  (gs://pub/gsutil.tar.gz and gs://pub/gsutil.zip) will contain the latest
  release. Also, the gs://pub bucket is now publicly readable (so, anyone
  can list its contents).


Release 2.0 (release-date: 2012-01-13)
======================================

New Features
------------

- Support for two new installation modes: enterprise and RPM.
  Customers can now install gsutil one of three ways:
  - Individual user mode (previously the only available mode): unpacking from
    a gzipped tarball (gs://pub/gsutil.tar.gz) or zip file
    (gs://pub/gsutil.zip) and running the gsutil command in place in the
    unpacked gsutil directory.
  - Enterprise mode (new): unpacking as above, and then running the setup.py
    script in the unpacked gsutil directory. This allows a systems
    administrator to install gsutil in a central location, using the Python
    distutils facility. This mode is supported only on Linux and MacOS.
  - RPM mode (new). A RedHat RPM can be built from the gsutil.spec.in file
    in the unpacked gsutil directory, allowing it to be installed as part of
    a RedHat build.

- Note: v2.0 is the first numbered gsutil release. Previous releases
  were given timestamps for versions. Numbered releases enable downstream
  package builds (like RPMs) to define dependencies more easily.
  This is also the first version where we began including release notes.
