release_tracks: ${release_tracks}
arguments:
- group:
    mutex: true
    required: true
    arguments:
    - group:
        arguments:
        - name: ${surface_spec_resource_arg}
          resource_arg: true
          positional: true
          required: false
    - name: all
- name: path
  required: false
- name: resource-format
