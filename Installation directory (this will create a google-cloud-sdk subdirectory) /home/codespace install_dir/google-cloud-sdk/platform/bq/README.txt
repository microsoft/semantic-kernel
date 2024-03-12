bq - command-line utilities to access BigQuery service
Copyright 2011-2016 Google Inc.
https://cloud.google.com/bigquery/bq-command-line-tool-quickstart


Running bq from the command line
=====================================

1. Try out bq by displaying a list of available commands. Type:
  bq

2. To display help information about a particular command, type:
  bq help command_name

Authorizing bq to access your BigQuery data
=====================================

While the bq tool can be used without any setup, it is highly recommended
that you create and store authorization credentials to access your BigQuery
data. This can be done by using the 'bq init' command.

1. To create and store authorization credentials, type:
 gcloud init

2. This will provide a URL where you can authorize gcloud to act on your behalf
when accessing the BigQuery API. Visit this URL in a web browser, copy the
resulting code, and paste it on the command line when prompted by gcloud.

3. This step will store an OAuth token a file, which
will remain valid until revoked by the user.

Basic bq commands
=====================================

Note: If you have not run "bq init" (see above) to store authorization
credentials, you will be asked to do before any operation involving data.

The following commands have additional options. For more information about
a specific command type:
  bq help command_name

1. You can run a query using the 'bq query' command:
  bq query 'select count(*) from publicdata:samples.shakespeare'

2. To list objects present in a collection, use 'bq ls':
  bq ls

3. Create a new table or dataset with 'bq mk':
  bq mk my_new_dataset

4. Load data from a source URI to a destination table with 'bq load':
  bq load <destination_table> <source_uri> <schema>

Running bq in shell mode
=====================================

1. bq can be run in an interactive shell mode. To enter shell mode, type:
  bq shell

2. In shell mode, you will be presented a command prompt, which will display
your default project GUID and dataset, if these values have been set. For
example:
  projectguid> help
  projectguid> ls
  projectguid> query 'select count(*) from publicdata:samples.shakespeare'
