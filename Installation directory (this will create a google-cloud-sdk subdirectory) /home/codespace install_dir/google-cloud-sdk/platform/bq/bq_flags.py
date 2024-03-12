#!/usr/bin/env python
"""Flags for calling BigQuery."""

import os
from typing import Optional



from absl import flags

_APILOG = flags.DEFINE_string(
    'apilog',
    None,
    (
        'Log all API requests and responses to the file specified by this flag.'
        ' Also accepts "stdout" and "stderr". Specifying the empty string will'
        ' direct to stdout.'
    ),
)
API: flags.FlagHolder[Optional[str]] = flags.DEFINE_string(
    'api',
    'https://www.googleapis.com',
    'API endpoint to talk to.'
)
_API_VERSION = flags.DEFINE_string('api_version', 'v2', 'API version to use.')
_DEBUG_MODE = flags.DEFINE_boolean(
    'debug_mode', False, 'Show tracebacks on Python exceptions.'
)
_TRACE = flags.DEFINE_string(
    'trace',
    None,
    'A tracing token '
    'to include in api requests.'
)
_HTTPLIB2_DEBUGLEVEL = flags.DEFINE_integer(
    'httplib2_debuglevel',
    None,
    (
        'Instruct httplib2 to print debugging messages by setting debuglevel to'
        ' the given value.'
    ),
)

_BIGQUERYRC = flags.DEFINE_string(
    'bigqueryrc',
    os.path.join(os.path.expanduser('~'), '.bigqueryrc'),
    (
        'Path to configuration file. The configuration file specifies new'
        ' defaults for any flags, and can be overrridden by specifying the flag'
        ' on the command line. If the --bigqueryrc flag is not specified, the'
        ' BIGQUERYRC environment variable is used. If that is not specified,'
        ' the path "~/.bigqueryrc" is used.'
    ),
)
_DISCOVERY_FILE = flags.DEFINE_string(
    'discovery_file',
    '',
    (
        'Filename for JSON document to read for the base BigQuery '
        'API discovery, excluding Model, Routine, RowAccessPolicy, '
        'and IAMPolicy APIs.'
    ),
)

_DISABLE_SSL_VALIDATION = flags.DEFINE_boolean(
    'disable_ssl_validation',
    False,
    'Disables HTTPS certificates validation. This is off by default.',
)
_CA_CERTIFICATES_FILE = flags.DEFINE_string(
    'ca_certificates_file', '', 'Location of CA certificates file.'
)
_PROXY_ADDRESS = flags.DEFINE_string(
    'proxy_address',
    '',
    'The name or IP address of the proxy host to use for connecting to GCP.',
)
_PROXY_PORT = flags.DEFINE_string(
    'proxy_port', '', 'The port number to use to connect to the proxy host.'
)
_PROXY_USERNAME = flags.DEFINE_string(
    'proxy_username',
    '',
    'The user name to use when authenticating with proxy host.',
)
_PROXY_PASSWORD = flags.DEFINE_string(
    'proxy_password',
    '',
    'The password to use when authenticating with proxy host.',
)

_SYNCHRONOUS_MODE = flags.DEFINE_boolean(
    'synchronous_mode',
    True,
    (
        'If True, wait for command completion before returning, and use the '
        'job completion status for error codes. If False, simply create the '
        'job, and use the success of job creation as the error code.'
    ),
    short_name='sync',
)
_PROJECT_ID = flags.DEFINE_string(
    'project_id', '', 'Default project to use for requests.'
)
_DATASET_ID = flags.DEFINE_string(
    'dataset_id',
    '',
    (
        'Default dataset reference to use for requests (Ignored when not'
        ' applicable.). Can be set as "project:dataset" or "dataset". If'
        ' project is missing, the value of the project_id flag will be used.'
    ),
)
_LOCATION = flags.DEFINE_string(
    'location',
    None,
    (
        'Default geographic location to use when creating datasets or'
        ' determining where jobs should run (Ignored when not applicable.)'
    ),
)
_USE_REGIONAL_ENDPOINTS = flags.DEFINE_boolean(
    'use_regional_endpoints',
    False,
    "Use a regional endpoint based on the operation's location.",
)

# This flag is "hidden" at the global scope to avoid polluting help
# text on individual commands for rarely used functionality.
_JOB_ID = flags.DEFINE_string(
    'job_id',
    None,
    (
        'A unique job_id to use for the request. If not specified, this client '
        'will generate a job_id. Applies only to commands that launch jobs, '
        'such as cp, extract, load, and query.'
    ),
)
_FINGERPRINT_JOB_ID = flags.DEFINE_boolean(
    'fingerprint_job_id',
    False,
    (
        'Whether to use a job id that is derived from a fingerprint of the job'
        ' configuration. This will prevent the same job from running multiple'
        ' times accidentally.'
    ),
)
_QUIET = flags.DEFINE_boolean(
    'quiet',
    False,
    'If True, ignore status updates while jobs are running.',
    short_name='q',
)
_HEADLESS = flags.DEFINE_boolean(
    'headless',
    False,
    (
        'Whether this bq session is running without user interaction. This '
        'affects behavior that expects user interaction, like whether '
        'debug_mode will break into the debugger and lowers the frequency '
        'of informational printing.'
    ),
)
_FORMAT = flags.DEFINE_enum(
    'format',
    None,
    ['none', 'json', 'prettyjson', 'csv', 'sparse', 'pretty'],
    (
        'Format for command output. Options include:'
        '\n pretty: formatted table output'
        '\n sparse: simpler table output'
        '\n prettyjson: easy-to-read JSON format'
        '\n json: maximally compact JSON'
        '\n csv: csv format with header'
        '\nThe first three are intended to be human-readable, and the latter '
        'three are for passing to another program. If no format is selected, '
        'one will be chosen based on the command run.'
    ),
)
_JOB_PROPERTY = flags.DEFINE_multi_string(
    'job_property',
    None,
    (
        'Additional key-value pairs to include in the properties field of '
        'the job configuration'
    ),
)  # No period: Multistring adds flagspec suffix.
_ENABLE_RESUMABLE_UPLOADS = flags.DEFINE_boolean(
    'enable_resumable_uploads',
    None,
    'Enables resumable uploads over HTTP (Only applies to load jobs that load '
    'data from local files.). Defaults to True.'
)
_MAX_ROWS_PER_REQUEST = flags.DEFINE_integer(
    'max_rows_per_request',
    None,
    'Specifies the max number of rows to return per read.',
)

_JOBS_QUERY_USE_RESULTS_FROM_RESPONSE = flags.DEFINE_boolean(
    'jobs_query_use_results_from_response',
    True,
    'If true, results from jobs.query response are used.',
)
_JOBS_QUERY_USE_REQUEST_ID = flags.DEFINE_boolean(
    'jobs_query_use_request_id',
    False,
    'If true, sends request_id in jobs.query request.',
)
ENABLE_GDRIVE = flags.DEFINE_boolean(
    'enable_gdrive',
    True,
    (
        'When set to true, requests new OAuth token with GDrive scope. '
        'When set to false, requests new OAuth token without GDrive scope.'
    ),
)
_MTLS = flags.DEFINE_boolean(
    'mtls',
    False,
    'If set will use mtls client certificate on connections to BigQuery.',
)



