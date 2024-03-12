#!/bin/fish
# The begin/end block limits the scope of all variables except $PATH
begin
  # This script aims to be a direct mapping of our path.bash.inc shell, rather
  # than idiomatic fish. Why? I don't really understand fish.
  set script_link (readlink (status -f)); or set script_link (status -f)
  # This sed expression is the equivalent of "${script_link%/*}" in bash, which
  # chops off "/*" (with * as a wildcard) from the end of script_link.
  set apparent_sdk_dir (echo $script_link | sed 's/\(.*\)\/.*/\1/')
  if [ "$apparent_sdk_dir" = "$script_link" ]
    set apparent_sdk_dir .
  end
  set old_dir (pwd)
  # No "cd -P" in fish. It always resolves symlinks to their canonical location,
  # though, when you "cd" in.
  # Also, cd is  cd is *both* a shell builtin and shell wrapper function (to
  # implement "cd -") in fish, so "command cd" won't work. "builtin cd" will.
  set sdk_dir (builtin cd "$apparent_sdk_dir" > /dev/null; and pwd)
  builtin cd "$old_dir"
  set bin_path "$sdk_dir/bin"
  # -gx for global (not limited to this begin/end block) and exportable (part of
  # the environment for child processes)
  if not contains "$bin_path" $PATH
    set -gx PATH "$bin_path" $PATH
  end
end
