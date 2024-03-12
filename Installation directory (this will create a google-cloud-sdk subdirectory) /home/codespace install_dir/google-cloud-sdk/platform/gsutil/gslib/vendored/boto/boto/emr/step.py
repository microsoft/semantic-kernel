# Copyright (c) 2010 Spotify AB
# Copyright (c) 2010-2011 Yelp
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

from boto.compat import six


class Step(object):
    """
    Jobflow Step base class
    """
    def jar(self):
        """
        :rtype: str
        :return: URI to the jar
        """
        raise NotImplemented()

    def args(self):
        """
        :rtype: list(str)
        :return: List of arguments for the step
        """
        raise NotImplemented()

    def main_class(self):
        """
        :rtype: str
        :return: The main class name
        """
        raise NotImplemented()


class JarStep(Step):
    """
    Custom jar step
    """
    def __init__(self, name, jar, main_class=None,
                 action_on_failure='TERMINATE_JOB_FLOW', step_args=None):
        """
        A elastic mapreduce step that executes a jar

        :type name: str
        :param name: The name of the step
        :type jar: str
        :param jar: S3 URI to the Jar file
        :type main_class: str
        :param main_class: The class to execute in the jar
        :type action_on_failure: str
        :param action_on_failure: An action, defined in the EMR docs to
            take on failure.
        :type step_args: list(str)
        :param step_args: A list of arguments to pass to the step
        """
        self.name = name
        self._jar = jar
        self._main_class = main_class
        self.action_on_failure = action_on_failure

        if isinstance(step_args, six.string_types):
            step_args = [step_args]

        self.step_args = step_args

    def jar(self):
        return self._jar

    def args(self):
        args = []

        if self.step_args:
            args.extend(self.step_args)

        return args

    def main_class(self):
        return self._main_class


class StreamingStep(Step):
    """
    Hadoop streaming step
    """
    def __init__(self, name, mapper, reducer=None, combiner=None,
                 action_on_failure='TERMINATE_JOB_FLOW',
                 cache_files=None, cache_archives=None,
                 step_args=None, input=None, output=None,
                 jar='/home/hadoop/contrib/streaming/hadoop-streaming.jar'):
        """
        A hadoop streaming elastic mapreduce step

        :type name: str
        :param name: The name of the step
        :type mapper: str
        :param mapper: The mapper URI
        :type reducer: str
        :param reducer: The reducer URI
        :type combiner: str
        :param combiner: The combiner URI. Only works for Hadoop 0.20
            and later!
        :type action_on_failure: str
        :param action_on_failure: An action, defined in the EMR docs to
            take on failure.
        :type cache_files: list(str)
        :param cache_files: A list of cache files to be bundled with the job
        :type cache_archives: list(str)
        :param cache_archives: A list of jar archives to be bundled with
            the job
        :type step_args: list(str)
        :param step_args: A list of arguments to pass to the step
        :type input: str or a list of str
        :param input: The input uri
        :type output: str
        :param output: The output uri
        :type jar: str
        :param jar: The hadoop streaming jar. This can be either a local
            path on the master node, or an s3:// URI.
        """
        self.name = name
        self.mapper = mapper
        self.reducer = reducer
        self.combiner = combiner
        self.action_on_failure = action_on_failure
        self.cache_files = cache_files
        self.cache_archives = cache_archives
        self.input = input
        self.output = output
        self._jar = jar

        if isinstance(step_args, six.string_types):
            step_args = [step_args]

        self.step_args = step_args

    def jar(self):
        return self._jar

    def main_class(self):
        return None

    def args(self):
        args = []

        # put extra args BEFORE -mapper and -reducer so that e.g. -libjar
        # will work
        if self.step_args:
            args.extend(self.step_args)

        args.extend(['-mapper', self.mapper])

        if self.combiner:
            args.extend(['-combiner', self.combiner])

        if self.reducer:
            args.extend(['-reducer', self.reducer])
        else:
            args.extend(['-jobconf', 'mapred.reduce.tasks=0'])

        if self.input:
            if isinstance(self.input, list):
                for input in self.input:
                    args.extend(('-input', input))
            else:
                args.extend(('-input', self.input))
        if self.output:
            args.extend(('-output', self.output))

        if self.cache_files:
            for cache_file in self.cache_files:
                args.extend(('-cacheFile', cache_file))

        if self.cache_archives:
            for cache_archive in self.cache_archives:
                args.extend(('-cacheArchive', cache_archive))

        return args

    def __repr__(self):
        return '%s.%s(name=%r, mapper=%r, reducer=%r, action_on_failure=%r, cache_files=%r, cache_archives=%r, step_args=%r, input=%r, output=%r, jar=%r)' % (
            self.__class__.__module__, self.__class__.__name__,
            self.name, self.mapper, self.reducer, self.action_on_failure,
            self.cache_files, self.cache_archives, self.step_args,
            self.input, self.output, self._jar)


class ScriptRunnerStep(JarStep):

    ScriptRunnerJar = 's3n://us-east-1.elasticmapreduce/libs/script-runner/script-runner.jar'

    def __init__(self, name, **kw):
        super(ScriptRunnerStep, self).__init__(name, self.ScriptRunnerJar, **kw)


class PigBase(ScriptRunnerStep):

    BaseArgs = ['s3n://us-east-1.elasticmapreduce/libs/pig/pig-script',
                '--base-path', 's3n://us-east-1.elasticmapreduce/libs/pig/']


class InstallPigStep(PigBase):
    """
    Install pig on emr step
    """

    InstallPigName = 'Install Pig'

    def __init__(self, pig_versions='latest'):
        step_args = []
        step_args.extend(self.BaseArgs)
        step_args.extend(['--install-pig'])
        step_args.extend(['--pig-versions', pig_versions])
        super(InstallPigStep, self).__init__(self.InstallPigName, step_args=step_args)


class PigStep(PigBase):
    """
    Pig script step
    """

    def __init__(self, name, pig_file, pig_versions='latest', pig_args=[]):
        step_args = []
        step_args.extend(self.BaseArgs)
        step_args.extend(['--pig-versions', pig_versions])
        step_args.extend(['--run-pig-script', '--args', '-f', pig_file])
        step_args.extend(pig_args)
        super(PigStep, self).__init__(name, step_args=step_args)


class HiveBase(ScriptRunnerStep):

    BaseArgs = ['s3n://us-east-1.elasticmapreduce/libs/hive/hive-script',
                '--base-path', 's3n://us-east-1.elasticmapreduce/libs/hive/']


class InstallHiveStep(HiveBase):
    """
    Install Hive on EMR step
    """
    InstallHiveName = 'Install Hive'

    def __init__(self, hive_versions='latest', hive_site=None):
        step_args = []
        step_args.extend(self.BaseArgs)
        step_args.extend(['--install-hive'])
        step_args.extend(['--hive-versions', hive_versions])
        if hive_site is not None:
            step_args.extend(['--hive-site=%s' % hive_site])
        super(InstallHiveStep, self).__init__(self.InstallHiveName,
                                  step_args=step_args)


class HiveStep(HiveBase):
    """
    Hive script step
    """

    def __init__(self, name, hive_file, hive_versions='latest',
                 hive_args=None):
        step_args = []
        step_args.extend(self.BaseArgs)
        step_args.extend(['--hive-versions', hive_versions])
        step_args.extend(['--run-hive-script', '--args', '-f', hive_file])
        if hive_args is not None:
            step_args.extend(hive_args)
        super(HiveStep, self).__init__(name, step_args=step_args)
