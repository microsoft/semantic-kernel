provider "google" {
  project = "${project}"
  region  = "${region}"
  zone    = "${zone}"
% if user_override:
  user_project_override = "${user_override}"
% endif
% if billing_project:
  billing_project = "${billing_project}"
% endif
}
