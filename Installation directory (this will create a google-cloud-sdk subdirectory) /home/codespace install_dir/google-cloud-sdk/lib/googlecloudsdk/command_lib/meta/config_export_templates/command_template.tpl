release_tracks: ${release_tracks}
command_type: CONFIG_EXPORT
help_text:
  brief: Export the configuration for ${api_a_or_an} ${branded_api_name} ${singular_name_with_spaces}.
  description: |
    *{command}* exports the configuration for ${api_a_or_an} ${branded_api_name} ${singular_name_with_spaces}.

    ${singular_capitalized_name} configurations can be exported in
    Kubernetes Resource Model (krm) or Terraform HCL formats. The
    default format is `krm`.

    Specifying `--all` allows you to export the configurations for all
    ${plural_resource_name_with_spaces} within the project.

    Specifying `--path` allows you to export the configuration(s) to
    a local directory.
  examples: |
    To export the configuration for ${resource_a_or_an} ${singular_name_with_spaces}, run:

      $ {command} ${resource_argument_name}

    To export the configuration for ${resource_a_or_an} ${singular_name_with_spaces} to a file, run:

      $ {command} ${resource_argument_name} --path=/path/to/dir/

    To export the configuration for ${resource_a_or_an} ${singular_name_with_spaces} in Terraform
    HCL format, run:

      $ {command} ${resource_argument_name} --resource-format=terraform

    To export the configurations for all ${plural_resource_name_with_spaces} within a
    project, run:

      $ {command} --all
arguments:
  resource:
    help_text: ${singular_capitalized_name} to export the configuration for.
    spec: !REF googlecloudsdk.command_lib.${resource_spec_path}
