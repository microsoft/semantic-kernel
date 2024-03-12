
Ruby Externalized Runtime
============================

This is the Ruby runtime definition that is used by gcloud to generate
Dockerfiles for GAE.

How to Run Tests
============================

In order to test your runtime changes you will need to run the following
commands.

```
$ sudo apt-get install python-pip
$ sudo pip install virtualenv
$ cd $CODE_DIRECTORY
$ git clone $GIT_HOST/ext-runtime-sdk
$ virtualenv test_env
$ . test_env/bin/activate
(test_env)$ pip install ext-runtime-sdk/
(test_env)$ pip install PyYaml appengine-config-transformer
(test_env)$ cd gae-xrt-ruby
(test_env)$ python test/runtime_test.py
```
