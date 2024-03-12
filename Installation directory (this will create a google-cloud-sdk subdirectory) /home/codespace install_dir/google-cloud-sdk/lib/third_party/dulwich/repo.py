# repo.py -- For dealing with git repositories.
# Copyright (C) 2007 James Westby <jw+debian@jameswestby.net>
# Copyright (C) 2008-2013 Jelmer Vernooij <jelmer@jelmer.uk>
#
# Dulwich is dual-licensed under the Apache License, Version 2.0 and the GNU
# General Public License as public by the Free Software Foundation; version 2.0
# or (at your option) any later version. You can redistribute it and/or
# modify it under the terms of either of these two licenses.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# You should have received a copy of the licenses; if not, see
# <http://www.gnu.org/licenses/> for a copy of the GNU General Public License
# and <http://www.apache.org/licenses/LICENSE-2.0> for a copy of the Apache
# License, Version 2.0.
#


"""Repository access.

This module contains the base class for git repositories
(BaseRepo) and an implementation which uses a repository on
local disk (Repo).

"""

from io import BytesIO
import os
import sys
import stat
import time
from typing import Optional, Tuple, TYPE_CHECKING, List, Dict, Union, Iterable

if TYPE_CHECKING:
    # There are no circular imports here, but we try to defer imports as long
    # as possible to reduce start-up time for anything that doesn't need
    # these imports.
    from dulwich.config import StackedConfig, ConfigFile
    from dulwich.index import Index

from dulwich.errors import (
    NoIndexPresent,
    NotBlobError,
    NotCommitError,
    NotGitRepository,
    NotTreeError,
    NotTagError,
    CommitError,
    RefFormatError,
    HookError,
)
from dulwich.file import (
    GitFile,
)
from dulwich.object_store import (
    DiskObjectStore,
    MemoryObjectStore,
    BaseObjectStore,
    ObjectStoreGraphWalker,
)
from dulwich.objects import (
    check_hexsha,
    valid_hexsha,
    Blob,
    Commit,
    ShaFile,
    Tag,
    Tree,
)
from dulwich.pack import (
    pack_objects_to_data,
)

from dulwich.hooks import (
    Hook,
    PreCommitShellHook,
    PostCommitShellHook,
    CommitMsgShellHook,
    PostReceiveShellHook,
)

from dulwich.line_ending import BlobNormalizer

from dulwich.refs import (  # noqa: F401
    ANNOTATED_TAG_SUFFIX,
    check_ref_format,
    RefsContainer,
    DictRefsContainer,
    InfoRefsContainer,
    DiskRefsContainer,
    read_packed_refs,
    read_packed_refs_with_peeled,
    write_packed_refs,
    SYMREF,
)


import warnings


CONTROLDIR = ".git"
OBJECTDIR = "objects"
REFSDIR = "refs"
REFSDIR_TAGS = "tags"
REFSDIR_HEADS = "heads"
INDEX_FILENAME = "index"
COMMONDIR = "commondir"
GITDIR = "gitdir"
WORKTREES = "worktrees"

BASE_DIRECTORIES = [
    ["branches"],
    [REFSDIR],
    [REFSDIR, REFSDIR_TAGS],
    [REFSDIR, REFSDIR_HEADS],
    ["hooks"],
    ["info"],
]

DEFAULT_REF = b"refs/heads/master"


class InvalidUserIdentity(Exception):
    """User identity is not of the format 'user <email>'"""

    def __init__(self, identity):
        self.identity = identity


def _get_default_identity() -> Tuple[str, str]:
    import getpass
    import socket

    username = getpass.getuser()
    try:
        import pwd
    except ImportError:
        fullname = None
    else:
        try:
            gecos = pwd.getpwnam(username).pw_gecos
        except KeyError:
            fullname = None
        else:
            fullname = gecos.split(",")[0]
    if not fullname:
        fullname = username
    email = os.environ.get("EMAIL")
    if email is None:
        email = "{}@{}".format(username, socket.gethostname())
    return (fullname, email)


def get_user_identity(config: "StackedConfig", kind: Optional[str] = None) -> bytes:
    """Determine the identity to use for new commits.

    If kind is set, this first checks
    GIT_${KIND}_NAME and GIT_${KIND}_EMAIL.

    If those variables are not set, then it will fall back
    to reading the user.name and user.email settings from
    the specified configuration.

    If that also fails, then it will fall back to using
    the current users' identity as obtained from the host
    system (e.g. the gecos field, $EMAIL, $USER@$(hostname -f).

    Args:
      kind: Optional kind to return identity for,
        usually either "AUTHOR" or "COMMITTER".

    Returns:
      A user identity
    """
    user = None  # type: Optional[bytes]
    email = None  # type: Optional[bytes]
    if kind:
        user_uc = os.environ.get("GIT_" + kind + "_NAME")
        if user_uc is not None:
            user = user_uc.encode("utf-8")
        email_uc = os.environ.get("GIT_" + kind + "_EMAIL")
        if email_uc is not None:
            email = email_uc.encode("utf-8")
    if user is None:
        try:
            user = config.get(("user",), "name")
        except KeyError:
            user = None
    if email is None:
        try:
            email = config.get(("user",), "email")
        except KeyError:
            email = None
    default_user, default_email = _get_default_identity()
    if user is None:
        user = default_user.encode("utf-8")
    if email is None:
        email = default_email.encode("utf-8")
    if email.startswith(b"<") and email.endswith(b">"):
        email = email[1:-1]
    return user + b" <" + email + b">"


def check_user_identity(identity):
    """Verify that a user identity is formatted correctly.

    Args:
      identity: User identity bytestring
    Raises:
      InvalidUserIdentity: Raised when identity is invalid
    """
    try:
        fst, snd = identity.split(b" <", 1)
    except ValueError:
        raise InvalidUserIdentity(identity)
    if b">" not in snd:
        raise InvalidUserIdentity(identity)


def parse_graftpoints(
    graftpoints: Iterable[bytes],
) -> Dict[bytes, List[bytes]]:
    """Convert a list of graftpoints into a dict

    Args:
      graftpoints: Iterator of graftpoint lines

    Each line is formatted as:
        <commit sha1> <parent sha1> [<parent sha1>]*

    Resulting dictionary is:
        <commit sha1>: [<parent sha1>*]

    https://git.wiki.kernel.org/index.php/GraftPoint
    """
    grafts = {}
    for line in graftpoints:
        raw_graft = line.split(None, 1)

        commit = raw_graft[0]
        if len(raw_graft) == 2:
            parents = raw_graft[1].split()
        else:
            parents = []

        for sha in [commit] + parents:
            check_hexsha(sha, "Invalid graftpoint")

        grafts[commit] = parents
    return grafts


def serialize_graftpoints(graftpoints: Dict[bytes, List[bytes]]) -> bytes:
    """Convert a dictionary of grafts into string

    The graft dictionary is:
        <commit sha1>: [<parent sha1>*]

    Each line is formatted as:
        <commit sha1> <parent sha1> [<parent sha1>]*

    https://git.wiki.kernel.org/index.php/GraftPoint

    """
    graft_lines = []
    for commit, parents in graftpoints.items():
        if parents:
            graft_lines.append(commit + b" " + b" ".join(parents))
        else:
            graft_lines.append(commit)
    return b"\n".join(graft_lines)


def _set_filesystem_hidden(path):
    """Mark path as to be hidden if supported by platform and filesystem.

    On win32 uses SetFileAttributesW api:
    <https://docs.microsoft.com/windows/desktop/api/fileapi/nf-fileapi-setfileattributesw>
    """
    if sys.platform == "win32":
        import ctypes
        from ctypes.wintypes import BOOL, DWORD, LPCWSTR

        FILE_ATTRIBUTE_HIDDEN = 2
        SetFileAttributesW = ctypes.WINFUNCTYPE(BOOL, LPCWSTR, DWORD)(
            ("SetFileAttributesW", ctypes.windll.kernel32)
        )

        if isinstance(path, bytes):
            path = os.fsdecode(path)
        if not SetFileAttributesW(path, FILE_ATTRIBUTE_HIDDEN):
            pass  # Could raise or log `ctypes.WinError()` here

    # Could implement other platform specific filesytem hiding here


class ParentsProvider(object):
    def __init__(self, store, grafts={}, shallows=[]):
        self.store = store
        self.grafts = grafts
        self.shallows = set(shallows)

    def get_parents(self, commit_id, commit=None):
        try:
            return self.grafts[commit_id]
        except KeyError:
            pass
        if commit_id in self.shallows:
            return []
        if commit is None:
            commit = self.store[commit_id]
        return commit.parents


class BaseRepo(object):
    """Base class for a git repository.

    :ivar object_store: Dictionary-like object for accessing
        the objects
    :ivar refs: Dictionary-like object with the refs in this
        repository
    """

    def __init__(self, object_store: BaseObjectStore, refs: RefsContainer):
        """Open a repository.

        This shouldn't be called directly, but rather through one of the
        base classes, such as MemoryRepo or Repo.

        Args:
          object_store: Object store to use
          refs: Refs container to use
        """
        self.object_store = object_store
        self.refs = refs

        self._graftpoints = {}  # type: Dict[bytes, List[bytes]]
        self.hooks = {}  # type: Dict[str, Hook]

    def _determine_file_mode(self) -> bool:
        """Probe the file-system to determine whether permissions can be trusted.

        Returns: True if permissions can be trusted, False otherwise.
        """
        raise NotImplementedError(self._determine_file_mode)

    def _init_files(self, bare: bool) -> None:
        """Initialize a default set of named files."""
        from dulwich.config import ConfigFile

        self._put_named_file("description", b"Unnamed repository")
        f = BytesIO()
        cf = ConfigFile()
        cf.set("core", "repositoryformatversion", "0")
        if self._determine_file_mode():
            cf.set("core", "filemode", True)
        else:
            cf.set("core", "filemode", False)

        cf.set("core", "bare", bare)
        cf.set("core", "logallrefupdates", True)
        cf.write_to_file(f)
        self._put_named_file("config", f.getvalue())
        self._put_named_file(os.path.join("info", "exclude"), b"")

    def get_named_file(self, path):
        """Get a file from the control dir with a specific name.

        Although the filename should be interpreted as a filename relative to
        the control dir in a disk-based Repo, the object returned need not be
        pointing to a file in that location.

        Args:
          path: The path to the file, relative to the control dir.
        Returns: An open file object, or None if the file does not exist.
        """
        raise NotImplementedError(self.get_named_file)

    def _put_named_file(self, path, contents):
        """Write a file to the control dir with the given name and contents.

        Args:
          path: The path to the file, relative to the control dir.
          contents: A string to write to the file.
        """
        raise NotImplementedError(self._put_named_file)

    def _del_named_file(self, path):
        """Delete a file in the contrl directory with the given name."""
        raise NotImplementedError(self._del_named_file)

    def open_index(self):
        """Open the index for this repository.

        Raises:
          NoIndexPresent: If no index is present
        Returns: The matching `Index`
        """
        raise NotImplementedError(self.open_index)

    def fetch(self, target, determine_wants=None, progress=None, depth=None):
        """Fetch objects into another repository.

        Args:
          target: The target repository
          determine_wants: Optional function to determine what refs to
            fetch.
          progress: Optional progress function
          depth: Optional shallow fetch depth
        Returns: The local refs
        """
        if determine_wants is None:
            determine_wants = target.object_store.determine_wants_all
        count, pack_data = self.fetch_pack_data(
            determine_wants,
            target.get_graph_walker(),
            progress=progress,
            depth=depth,
        )
        target.object_store.add_pack_data(count, pack_data, progress)
        return self.get_refs()

    def fetch_pack_data(
        self,
        determine_wants,
        graph_walker,
        progress,
        get_tagged=None,
        depth=None,
    ):
        """Fetch the pack data required for a set of revisions.

        Args:
          determine_wants: Function that takes a dictionary with heads
            and returns the list of heads to fetch.
          graph_walker: Object that can iterate over the list of revisions
            to fetch and has an "ack" method that will be called to acknowledge
            that a revision is present.
          progress: Simple progress function that will be called with
            updated progress strings.
          get_tagged: Function that returns a dict of pointed-to sha ->
            tag sha for including tags.
          depth: Shallow fetch depth
        Returns: count and iterator over pack data
        """
        # TODO(user): Fetch pack data directly, don't create objects first.
        objects = self.fetch_objects(
            determine_wants, graph_walker, progress, get_tagged, depth=depth
        )
        return pack_objects_to_data(objects)

    def fetch_objects(
        self,
        determine_wants,
        graph_walker,
        progress,
        get_tagged=None,
        depth=None,
    ):
        """Fetch the missing objects required for a set of revisions.

        Args:
          determine_wants: Function that takes a dictionary with heads
            and returns the list of heads to fetch.
          graph_walker: Object that can iterate over the list of revisions
            to fetch and has an "ack" method that will be called to acknowledge
            that a revision is present.
          progress: Simple progress function that will be called with
            updated progress strings.
          get_tagged: Function that returns a dict of pointed-to sha ->
            tag sha for including tags.
          depth: Shallow fetch depth
        Returns: iterator over objects, with __len__ implemented
        """
        if depth not in (None, 0):
            raise NotImplementedError("depth not supported yet")

        refs = {}
        for ref, sha in self.get_refs().items():
            try:
                obj = self.object_store[sha]
            except KeyError:
                warnings.warn(
                    "ref %s points at non-present sha %s"
                    % (ref.decode("utf-8", "replace"), sha.decode("ascii")),
                    UserWarning,
                )
                continue
            else:
                if isinstance(obj, Tag):
                    refs[ref + ANNOTATED_TAG_SUFFIX] = obj.object[1]
                refs[ref] = sha

        wants = determine_wants(refs)
        if not isinstance(wants, list):
            raise TypeError("determine_wants() did not return a list")

        shallows = getattr(graph_walker, "shallow", frozenset())
        unshallows = getattr(graph_walker, "unshallow", frozenset())

        if wants == []:
            # TODO(user): find a way to short-circuit that doesn't change
            # this interface.

            if shallows or unshallows:
                # Do not send a pack in shallow short-circuit path
                return None

            return []

        # If the graph walker is set up with an implementation that can
        # ACK/NAK to the wire, it will write data to the client through
        # this call as a side-effect.
        haves = self.object_store.find_common_revisions(graph_walker)

        # Deal with shallow requests separately because the haves do
        # not reflect what objects are missing
        if shallows or unshallows:
            # TODO: filter the haves commits from iter_shas. the specific
            # commits aren't missing.
            haves = []

        parents_provider = ParentsProvider(self.object_store, shallows=shallows)

        def get_parents(commit):
            return parents_provider.get_parents(commit.id, commit)

        return self.object_store.iter_shas(
            self.object_store.find_missing_objects(
                haves,
                wants,
                self.get_shallow(),
                progress,
                get_tagged,
                get_parents=get_parents,
            )
        )

    def generate_pack_data(self, have, want, progress=None, ofs_delta=None):
        """Generate pack data objects for a set of wants/haves.

        Args:
          have: List of SHA1s of objects that should not be sent
          want: List of SHA1s of objects that should be sent
          ofs_delta: Whether OFS deltas can be included
          progress: Optional progress reporting method
        """
        return self.object_store.generate_pack_data(
            have,
            want,
            shallow=self.get_shallow(),
            progress=progress,
            ofs_delta=ofs_delta,
        )

    def get_graph_walker(self, heads=None):
        """Retrieve a graph walker.

        A graph walker is used by a remote repository (or proxy)
        to find out which objects are present in this repository.

        Args:
          heads: Repository heads to use (optional)
        Returns: A graph walker object
        """
        if heads is None:
            heads = [
                sha
                for sha in self.refs.as_dict(b"refs/heads").values()
                if sha in self.object_store
            ]
        parents_provider = ParentsProvider(self.object_store)
        return ObjectStoreGraphWalker(
            heads, parents_provider.get_parents, shallow=self.get_shallow()
        )

    def get_refs(self) -> Dict[bytes, bytes]:
        """Get dictionary with all refs.

        Returns: A ``dict`` mapping ref names to SHA1s
        """
        return self.refs.as_dict()

    def head(self) -> bytes:
        """Return the SHA1 pointed at by HEAD."""
        return self.refs[b"HEAD"]

    def _get_object(self, sha, cls):
        assert len(sha) in (20, 40)
        ret = self.get_object(sha)
        if not isinstance(ret, cls):
            if cls is Commit:
                raise NotCommitError(ret)
            elif cls is Blob:
                raise NotBlobError(ret)
            elif cls is Tree:
                raise NotTreeError(ret)
            elif cls is Tag:
                raise NotTagError(ret)
            else:
                raise Exception(
                    "Type invalid: %r != %r" % (ret.type_name, cls.type_name)
                )
        return ret

    def get_object(self, sha: bytes) -> ShaFile:
        """Retrieve the object with the specified SHA.

        Args:
          sha: SHA to retrieve
        Returns: A ShaFile object
        Raises:
          KeyError: when the object can not be found
        """
        return self.object_store[sha]

    def parents_provider(self):
        return ParentsProvider(
            self.object_store,
            grafts=self._graftpoints,
            shallows=self.get_shallow(),
        )

    def get_parents(self, sha: bytes, commit: Commit = None) -> List[bytes]:
        """Retrieve the parents of a specific commit.

        If the specific commit is a graftpoint, the graft parents
        will be returned instead.

        Args:
          sha: SHA of the commit for which to retrieve the parents
          commit: Optional commit matching the sha
        Returns: List of parents
        """
        return self.parents_provider().get_parents(sha, commit)

    def get_config(self):
        """Retrieve the config object.

        Returns: `ConfigFile` object for the ``.git/config`` file.
        """
        raise NotImplementedError(self.get_config)

    def get_description(self):
        """Retrieve the description for this repository.

        Returns: String with the description of the repository
            as set by the user.
        """
        raise NotImplementedError(self.get_description)

    def set_description(self, description):
        """Set the description for this repository.

        Args:
          description: Text to set as description for this repository.
        """
        raise NotImplementedError(self.set_description)

    def get_config_stack(self) -> "StackedConfig":
        """Return a config stack for this repository.

        This stack accesses the configuration for both this repository
        itself (.git/config) and the global configuration, which usually
        lives in ~/.gitconfig.

        Returns: `Config` instance for this repository
        """
        from dulwich.config import StackedConfig

        backends = [self.get_config()] + StackedConfig.default_backends()
        return StackedConfig(backends, writable=backends[0])

    def get_shallow(self):
        """Get the set of shallow commits.

        Returns: Set of shallow commits.
        """
        f = self.get_named_file("shallow")
        if f is None:
            return set()
        with f:
            return set(line.strip() for line in f)

    def update_shallow(self, new_shallow, new_unshallow):
        """Update the list of shallow objects.

        Args:
          new_shallow: Newly shallow objects
          new_unshallow: Newly no longer shallow objects
        """
        shallow = self.get_shallow()
        if new_shallow:
            shallow.update(new_shallow)
        if new_unshallow:
            shallow.difference_update(new_unshallow)
        self._put_named_file("shallow", b"".join([sha + b"\n" for sha in shallow]))

    def get_peeled(self, ref):
        """Get the peeled value of a ref.

        Args:
          ref: The refname to peel.
        Returns: The fully-peeled SHA1 of a tag object, after peeling all
            intermediate tags; if the original ref does not point to a tag,
            this will equal the original SHA1.
        """
        cached = self.refs.get_peeled(ref)
        if cached is not None:
            return cached
        return self.object_store.peel_sha(self.refs[ref]).id

    def get_walker(self, include=None, *args, **kwargs):
        """Obtain a walker for this repository.

        Args:
          include: Iterable of SHAs of commits to include along with their
            ancestors. Defaults to [HEAD]
          exclude: Iterable of SHAs of commits to exclude along with their
            ancestors, overriding includes.
          order: ORDER_* constant specifying the order of results.
            Anything other than ORDER_DATE may result in O(n) memory usage.
          reverse: If True, reverse the order of output, requiring O(n)
            memory.
          max_entries: The maximum number of entries to yield, or None for
            no limit.
          paths: Iterable of file or subtree paths to show entries for.
          rename_detector: diff.RenameDetector object for detecting
            renames.
          follow: If True, follow path across renames/copies. Forces a
            default rename_detector.
          since: Timestamp to list commits after.
          until: Timestamp to list commits before.
          queue_cls: A class to use for a queue of commits, supporting the
            iterator protocol. The constructor takes a single argument, the
            Walker.
        Returns: A `Walker` object
        """
        from dulwich.walk import Walker

        if include is None:
            include = [self.head()]
        if isinstance(include, str):
            include = [include]

        kwargs["get_parents"] = lambda commit: self.get_parents(commit.id, commit)

        return Walker(self.object_store, include, *args, **kwargs)

    def __getitem__(self, name):
        """Retrieve a Git object by SHA1 or ref.

        Args:
          name: A Git object SHA1 or a ref name
        Returns: A `ShaFile` object, such as a Commit or Blob
        Raises:
          KeyError: when the specified ref or object does not exist
        """
        if not isinstance(name, bytes):
            raise TypeError(
                "'name' must be bytestring, not %.80s" % type(name).__name__
            )
        if len(name) in (20, 40):
            try:
                return self.object_store[name]
            except (KeyError, ValueError):
                pass
        try:
            return self.object_store[self.refs[name]]
        except RefFormatError:
            raise KeyError(name)

    def __contains__(self, name: bytes) -> bool:
        """Check if a specific Git object or ref is present.

        Args:
          name: Git object SHA1 or ref name
        """
        if len(name) == 20 or (len(name) == 40 and valid_hexsha(name)):
            return name in self.object_store or name in self.refs
        else:
            return name in self.refs

    def __setitem__(self, name: bytes, value: Union[ShaFile, bytes]):
        """Set a ref.

        Args:
          name: ref name
          value: Ref value - either a ShaFile object, or a hex sha
        """
        if name.startswith(b"refs/") or name == b"HEAD":
            if isinstance(value, ShaFile):
                self.refs[name] = value.id
            elif isinstance(value, bytes):
                self.refs[name] = value
            else:
                raise TypeError(value)
        else:
            raise ValueError(name)

    def __delitem__(self, name: bytes):
        """Remove a ref.

        Args:
          name: Name of the ref to remove
        """
        if name.startswith(b"refs/") or name == b"HEAD":
            del self.refs[name]
        else:
            raise ValueError(name)

    def _get_user_identity(self, config: "StackedConfig", kind: str = None) -> bytes:
        """Determine the identity to use for new commits."""
        # TODO(user): Deprecate this function in favor of get_user_identity
        return get_user_identity(config)

    def _add_graftpoints(self, updated_graftpoints: Dict[bytes, List[bytes]]):
        """Add or modify graftpoints

        Args:
          updated_graftpoints: Dict of commit shas to list of parent shas
        """

        # Simple validation
        for commit, parents in updated_graftpoints.items():
            for sha in [commit] + parents:
                check_hexsha(sha, "Invalid graftpoint")

        self._graftpoints.update(updated_graftpoints)

    def _remove_graftpoints(self, to_remove: List[bytes] = []) -> None:
        """Remove graftpoints

        Args:
          to_remove: List of commit shas
        """
        for sha in to_remove:
            del self._graftpoints[sha]

    def _read_heads(self, name):
        f = self.get_named_file(name)
        if f is None:
            return []
        with f:
            return [line.strip() for line in f.readlines() if line.strip()]

    def do_commit(  # noqa: C901
        self,
        message=None,
        committer=None,
        author=None,
        commit_timestamp=None,
        commit_timezone=None,
        author_timestamp=None,
        author_timezone=None,
        tree=None,
        encoding=None,
        ref=b"HEAD",
        merge_heads=None,
        no_verify=False,
    ):
        """Create a new commit.

        If not specified, `committer` and `author` default to
        get_user_identity(..., 'COMMITTER')
        and get_user_identity(..., 'AUTHOR') respectively.

        Args:
          message: Commit message
          committer: Committer fullname
          author: Author fullname
          commit_timestamp: Commit timestamp (defaults to now)
          commit_timezone: Commit timestamp timezone (defaults to GMT)
          author_timestamp: Author timestamp (defaults to commit
            timestamp)
          author_timezone: Author timestamp timezone
            (defaults to commit timestamp timezone)
          tree: SHA1 of the tree root to use (if not specified the
            current index will be committed).
          encoding: Encoding
          ref: Optional ref to commit to (defaults to current branch)
          merge_heads: Merge heads (defaults to .git/MERGE_HEADS)
          no_verify: Skip pre-commit and commit-msg hooks

        Returns:
          New commit SHA1
        """
        import time

        c = Commit()
        if tree is None:
            index = self.open_index()
            c.tree = index.commit(self.object_store)
        else:
            if len(tree) != 40:
                raise ValueError("tree must be a 40-byte hex sha string")
            c.tree = tree

        try:
            if not no_verify:
                self.hooks["pre-commit"].execute()
        except HookError as e:
            raise CommitError(e)
        except KeyError:  # no hook defined, silent fallthrough
            pass

        config = self.get_config_stack()
        if merge_heads is None:
            merge_heads = self._read_heads("MERGE_HEADS")
        if committer is None:
            committer = get_user_identity(config, kind="COMMITTER")
        check_user_identity(committer)
        c.committer = committer
        if commit_timestamp is None:
            # FIXME: Support GIT_COMMITTER_DATE environment variable
            commit_timestamp = time.time()
        c.commit_time = int(commit_timestamp)
        if commit_timezone is None:
            # FIXME: Use current user timezone rather than UTC
            commit_timezone = 0
        c.commit_timezone = commit_timezone
        if author is None:
            author = get_user_identity(config, kind="AUTHOR")
        c.author = author
        check_user_identity(author)
        if author_timestamp is None:
            # FIXME: Support GIT_AUTHOR_DATE environment variable
            author_timestamp = commit_timestamp
        c.author_time = int(author_timestamp)
        if author_timezone is None:
            author_timezone = commit_timezone
        c.author_timezone = author_timezone
        if encoding is None:
            try:
                encoding = config.get(("i18n",), "commitEncoding")
            except KeyError:
                pass  # No dice
        if encoding is not None:
            c.encoding = encoding
        if message is None:
            # FIXME: Try to read commit message from .git/MERGE_MSG
            raise ValueError("No commit message specified")

        try:
            if no_verify:
                c.message = message
            else:
                c.message = self.hooks["commit-msg"].execute(message)
                if c.message is None:
                    c.message = message
        except HookError as e:
            raise CommitError(e)
        except KeyError:  # no hook defined, message not modified
            c.message = message

        if ref is None:
            # Create a dangling commit
            c.parents = merge_heads
            self.object_store.add_object(c)
        else:
            try:
                old_head = self.refs[ref]
                c.parents = [old_head] + merge_heads
                self.object_store.add_object(c)
                ok = self.refs.set_if_equals(
                    ref,
                    old_head,
                    c.id,
                    message=b"commit: " + message,
                    committer=committer,
                    timestamp=commit_timestamp,
                    timezone=commit_timezone,
                )
            except KeyError:
                c.parents = merge_heads
                self.object_store.add_object(c)
                ok = self.refs.add_if_new(
                    ref,
                    c.id,
                    message=b"commit: " + message,
                    committer=committer,
                    timestamp=commit_timestamp,
                    timezone=commit_timezone,
                )
            if not ok:
                # Fail if the atomic compare-and-swap failed, leaving the
                # commit and all its objects as garbage.
                raise CommitError("%s changed during commit" % (ref,))

        self._del_named_file("MERGE_HEADS")

        try:
            self.hooks["post-commit"].execute()
        except HookError as e:  # silent failure
            warnings.warn("post-commit hook failed: %s" % e, UserWarning)
        except KeyError:  # no hook defined, silent fallthrough
            pass

        return c.id


def read_gitfile(f):
    """Read a ``.git`` file.

    The first line of the file should start with "gitdir: "

    Args:
      f: File-like object to read from
    Returns: A path
    """
    cs = f.read()
    if not cs.startswith("gitdir: "):
        raise ValueError("Expected file to start with 'gitdir: '")
    return cs[len("gitdir: ") :].rstrip("\n")


class UnsupportedVersion(Exception):
    """Unsupported repository version."""

    def __init__(self, version):
        self.version = version


class Repo(BaseRepo):
    """A git repository backed by local disk.

    To open an existing repository, call the contructor with
    the path of the repository.

    To create a new repository, use the Repo.init class method.
    """

    def __init__(self, root, object_store=None, bare=None):
        hidden_path = os.path.join(root, CONTROLDIR)
        if bare is None:
            if (os.path.isfile(hidden_path) or
                    os.path.isdir(os.path.join(hidden_path, OBJECTDIR))):
                bare = False
            elif (os.path.isdir(os.path.join(root, OBJECTDIR)) and
                    os.path.isdir(os.path.join(root, REFSDIR))):
                bare = True
            else:
                raise NotGitRepository(
                    "No git repository was found at %(path)s" % dict(path=root)
                )

        self.bare = bare
        if bare is False:
            if os.path.isfile(hidden_path):
                with open(hidden_path, "r") as f:
                    path = read_gitfile(f)
                self.bare = False
                self._controldir = os.path.join(root, path)
            else:
                self._controldir = hidden_path
        else:
            self._controldir = root
        commondir = self.get_named_file(COMMONDIR)
        if commondir is not None:
            with commondir:
                self._commondir = os.path.join(
                    self.controldir(),
                    os.fsdecode(commondir.read().rstrip(b"\r\n")),
                )
        else:
            self._commondir = self._controldir
        self.path = root
        config = self.get_config()
        try:
            format_version = int(config.get("core", "repositoryformatversion"))
        except KeyError:
            format_version = 0
        if format_version != 0:
            raise UnsupportedVersion(format_version)
        if object_store is None:
            object_store = DiskObjectStore.from_config(
                os.path.join(self.commondir(), OBJECTDIR), config
            )
        refs = DiskRefsContainer(
            self.commondir(), self._controldir, logger=self._write_reflog
        )
        BaseRepo.__init__(self, object_store, refs)

        self._graftpoints = {}
        graft_file = self.get_named_file(
            os.path.join("info", "grafts"), basedir=self.commondir()
        )
        if graft_file:
            with graft_file:
                self._graftpoints.update(parse_graftpoints(graft_file))
        graft_file = self.get_named_file("shallow", basedir=self.commondir())
        if graft_file:
            with graft_file:
                self._graftpoints.update(parse_graftpoints(graft_file))

        self.hooks["pre-commit"] = PreCommitShellHook(self.controldir())
        self.hooks["commit-msg"] = CommitMsgShellHook(self.controldir())
        self.hooks["post-commit"] = PostCommitShellHook(self.controldir())
        self.hooks["post-receive"] = PostReceiveShellHook(self.controldir())

    def _write_reflog(
        self, ref, old_sha, new_sha, committer, timestamp, timezone, message
    ):
        from .reflog import format_reflog_line

        path = os.path.join(self.controldir(), "logs", os.fsdecode(ref))
        try:
            os.makedirs(os.path.dirname(path))
        except FileExistsError:
            pass
        if committer is None:
            config = self.get_config_stack()
            committer = self._get_user_identity(config)
        check_user_identity(committer)
        if timestamp is None:
            timestamp = int(time.time())
        if timezone is None:
            timezone = 0  # FIXME
        with open(path, "ab") as f:
            f.write(
                format_reflog_line(
                    old_sha, new_sha, committer, timestamp, timezone, message
                )
                + b"\n"
            )

    @classmethod
    def discover(cls, start="."):
        """Iterate parent directories to discover a repository

        Return a Repo object for the first parent directory that looks like a
        Git repository.

        Args:
          start: The directory to start discovery from (defaults to '.')
        """
        remaining = True
        path = os.path.abspath(start)
        while remaining:
            try:
                return cls(path)
            except NotGitRepository:
                path, remaining = os.path.split(path)
        raise NotGitRepository(
            "No git repository was found at %(path)s" % dict(path=start)
        )

    def controldir(self):
        """Return the path of the control directory."""
        return self._controldir

    def commondir(self):
        """Return the path of the common directory.

        For a main working tree, it is identical to controldir().

        For a linked working tree, it is the control directory of the
        main working tree."""

        return self._commondir

    def _determine_file_mode(self):
        """Probe the file-system to determine whether permissions can be trusted.

        Returns: True if permissions can be trusted, False otherwise.
        """
        fname = os.path.join(self.path, ".probe-permissions")
        with open(fname, "w") as f:
            f.write("")

        st1 = os.lstat(fname)
        try:
            os.chmod(fname, st1.st_mode ^ stat.S_IXUSR)
        except PermissionError:
            return False
        st2 = os.lstat(fname)

        os.unlink(fname)

        mode_differs = st1.st_mode != st2.st_mode
        st2_has_exec = (st2.st_mode & stat.S_IXUSR) != 0

        return mode_differs and st2_has_exec

    def _put_named_file(self, path, contents):
        """Write a file to the control dir with the given name and contents.

        Args:
          path: The path to the file, relative to the control dir.
          contents: A string to write to the file.
        """
        path = path.lstrip(os.path.sep)
        with GitFile(os.path.join(self.controldir(), path), "wb") as f:
            f.write(contents)

    def _del_named_file(self, path):
        try:
            os.unlink(os.path.join(self.controldir(), path))
        except FileNotFoundError:
            return

    def get_named_file(self, path, basedir=None):
        """Get a file from the control dir with a specific name.

        Although the filename should be interpreted as a filename relative to
        the control dir in a disk-based Repo, the object returned need not be
        pointing to a file in that location.

        Args:
          path: The path to the file, relative to the control dir.
          basedir: Optional argument that specifies an alternative to the
            control dir.
        Returns: An open file object, or None if the file does not exist.
        """
        # TODO(user): sanitize filenames, since this is used directly by
        # the dumb web serving code.
        if basedir is None:
            basedir = self.controldir()
        path = path.lstrip(os.path.sep)
        try:
            return open(os.path.join(basedir, path), "rb")
        except FileNotFoundError:
            return None

    def index_path(self):
        """Return path to the index file."""
        return os.path.join(self.controldir(), INDEX_FILENAME)

    def open_index(self) -> "Index":
        """Open the index for this repository.

        Raises:
          NoIndexPresent: If no index is present
        Returns: The matching `Index`
        """
        from dulwich.index import Index

        if not self.has_index():
            raise NoIndexPresent()
        return Index(self.index_path())

    def has_index(self):
        """Check if an index is present."""
        # Bare repos must never have index files; non-bare repos may have a
        # missing index file, which is treated as empty.
        return not self.bare

    def stage(self, fs_paths):
        """Stage a set of paths.

        Args:
          fs_paths: List of paths, relative to the repository path
        """

        root_path_bytes = os.fsencode(self.path)

        if not isinstance(fs_paths, list):
            fs_paths = [fs_paths]
        from dulwich.index import (
            blob_from_path_and_stat,
            index_entry_from_stat,
            _fs_to_tree_path,
        )

        index = self.open_index()
        blob_normalizer = self.get_blob_normalizer()
        for fs_path in fs_paths:
            if not isinstance(fs_path, bytes):
                fs_path = os.fsencode(fs_path)
            if os.path.isabs(fs_path):
                raise ValueError(
                    "path %r should be relative to "
                    "repository root, not absolute" % fs_path
                )
            tree_path = _fs_to_tree_path(fs_path)
            full_path = os.path.join(root_path_bytes, fs_path)
            try:
                st = os.lstat(full_path)
            except OSError:
                # File no longer exists
                try:
                    del index[tree_path]
                except KeyError:
                    pass  # already removed
            else:
                if not stat.S_ISREG(st.st_mode) and not stat.S_ISLNK(st.st_mode):
                    try:
                        del index[tree_path]
                    except KeyError:
                        pass
                else:
                    blob = blob_from_path_and_stat(full_path, st)
                    blob = blob_normalizer.checkin_normalize(blob, fs_path)
                    self.object_store.add_object(blob)
                    index[tree_path] = index_entry_from_stat(st, blob.id, 0)
        index.write()

    def clone(
        self,
        target_path,
        mkdir=True,
        bare=False,
        origin=b"origin",
        checkout=None,
    ):
        """Clone this repository.

        Args:
          target_path: Target path
          mkdir: Create the target directory
          bare: Whether to create a bare repository
          origin: Base name for refs in target repository
            cloned from this repository
        Returns: Created repository as `Repo`
        """
        if not bare:
            target = self.init(target_path, mkdir=mkdir)
        else:
            if checkout:
                raise ValueError("checkout and bare are incompatible")
            target = self.init_bare(target_path, mkdir=mkdir)
        self.fetch(target)
        encoded_path = self.path
        if not isinstance(encoded_path, bytes):
            encoded_path = os.fsencode(encoded_path)
        ref_message = b"clone: from " + encoded_path
        target.refs.import_refs(
            b"refs/remotes/" + origin,
            self.refs.as_dict(b"refs/heads"),
            message=ref_message,
        )
        target.refs.import_refs(
            b"refs/tags", self.refs.as_dict(b"refs/tags"), message=ref_message
        )
        try:
            target.refs.add_if_new(
                DEFAULT_REF, self.refs[DEFAULT_REF], message=ref_message
            )
        except KeyError:
            pass
        target_config = target.get_config()
        target_config.set(("remote", "origin"), "url", encoded_path)
        target_config.set(
            ("remote", "origin"),
            "fetch",
            "+refs/heads/*:refs/remotes/origin/*",
        )
        target_config.write_to_path()

        # Update target head
        head_chain, head_sha = self.refs.follow(b"HEAD")
        if head_chain and head_sha is not None:
            target.refs.set_symbolic_ref(b"HEAD", head_chain[-1], message=ref_message)
            target[b"HEAD"] = head_sha

            if checkout is None:
                checkout = not bare
            if checkout:
                # Checkout HEAD to target dir
                target.reset_index()

        return target

    def reset_index(self, tree=None):
        """Reset the index back to a specific tree.

        Args:
          tree: Tree SHA to reset to, None for current HEAD tree.
        """
        from dulwich.index import (
            build_index_from_tree,
            validate_path_element_default,
            validate_path_element_ntfs,
        )

        if tree is None:
            tree = self[b"HEAD"].tree
        config = self.get_config()
        honor_filemode = config.get_boolean(b"core", b"filemode", os.name != "nt")
        if config.get_boolean(b"core", b"core.protectNTFS", os.name == "nt"):
            validate_path_element = validate_path_element_ntfs
        else:
            validate_path_element = validate_path_element_default
        return build_index_from_tree(
            self.path,
            self.index_path(),
            self.object_store,
            tree,
            honor_filemode=honor_filemode,
            validate_path_element=validate_path_element,
        )

    def get_config(self) -> "ConfigFile":
        """Retrieve the config object.

        Returns: `ConfigFile` object for the ``.git/config`` file.
        """
        from dulwich.config import ConfigFile

        path = os.path.join(self._controldir, "config")
        try:
            return ConfigFile.from_path(path)
        except FileNotFoundError:
            ret = ConfigFile()
            ret.path = path
            return ret

    def get_description(self):
        """Retrieve the description of this repository.

        Returns: A string describing the repository or None.
        """
        path = os.path.join(self._controldir, "description")
        try:
            with GitFile(path, "rb") as f:
                return f.read()
        except FileNotFoundError:
            return None

    def __repr__(self):
        return "<Repo at %r>" % self.path

    def set_description(self, description):
        """Set the description for this repository.

        Args:
          description: Text to set as description for this repository.
        """

        self._put_named_file("description", description)

    @classmethod
    def _init_maybe_bare(cls, path, controldir, bare, object_store=None):
        for d in BASE_DIRECTORIES:
            os.mkdir(os.path.join(controldir, *d))
        if object_store is None:
            object_store = DiskObjectStore.init(os.path.join(controldir, OBJECTDIR))
        ret = cls(path, bare=bare, object_store=object_store)
        ret.refs.set_symbolic_ref(b"HEAD", DEFAULT_REF)
        ret._init_files(bare)
        return ret

    @classmethod
    def init(cls, path, mkdir=False):
        """Create a new repository.

        Args:
          path: Path in which to create the repository
          mkdir: Whether to create the directory
        Returns: `Repo` instance
        """
        if mkdir:
            os.mkdir(path)
        controldir = os.path.join(path, CONTROLDIR)
        os.mkdir(controldir)
        _set_filesystem_hidden(controldir)
        return cls._init_maybe_bare(path, controldir, False)

    @classmethod
    def _init_new_working_directory(cls, path, main_repo, identifier=None, mkdir=False):
        """Create a new working directory linked to a repository.

        Args:
          path: Path in which to create the working tree.
          main_repo: Main repository to reference
          identifier: Worktree identifier
          mkdir: Whether to create the directory
        Returns: `Repo` instance
        """
        if mkdir:
            os.mkdir(path)
        if identifier is None:
            identifier = os.path.basename(path)
        main_worktreesdir = os.path.join(main_repo.controldir(), WORKTREES)
        worktree_controldir = os.path.join(main_worktreesdir, identifier)
        gitdirfile = os.path.join(path, CONTROLDIR)
        with open(gitdirfile, "wb") as f:
            f.write(b"gitdir: " + os.fsencode(worktree_controldir) + b"\n")
        try:
            os.mkdir(main_worktreesdir)
        except FileExistsError:
            pass
        try:
            os.mkdir(worktree_controldir)
        except FileExistsError:
            pass
        with open(os.path.join(worktree_controldir, GITDIR), "wb") as f:
            f.write(os.fsencode(gitdirfile) + b"\n")
        with open(os.path.join(worktree_controldir, COMMONDIR), "wb") as f:
            f.write(b"../..\n")
        with open(os.path.join(worktree_controldir, "HEAD"), "wb") as f:
            f.write(main_repo.head() + b"\n")
        r = cls(path)
        r.reset_index()
        return r

    @classmethod
    def init_bare(cls, path, mkdir=False, object_store=None):
        """Create a new bare repository.

        ``path`` should already exist and be an empty directory.

        Args:
          path: Path to create bare repository in
        Returns: a `Repo` instance
        """
        if mkdir:
            os.mkdir(path)
        return cls._init_maybe_bare(path, path, True, object_store=object_store)

    create = init_bare

    def close(self):
        """Close any files opened by this repository."""
        self.object_store.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def get_blob_normalizer(self):
        """Return a BlobNormalizer object"""
        # TODO Parse the git attributes files
        git_attributes = {}
        return BlobNormalizer(self.get_config_stack(), git_attributes)


class MemoryRepo(BaseRepo):
    """Repo that stores refs, objects, and named files in memory.

    MemoryRepos are always bare: they have no working tree and no index, since
    those have a stronger dependency on the filesystem.
    """

    def __init__(self):
        from dulwich.config import ConfigFile

        self._reflog = []
        refs_container = DictRefsContainer({}, logger=self._append_reflog)
        BaseRepo.__init__(self, MemoryObjectStore(), refs_container)
        self._named_files = {}
        self.bare = True
        self._config = ConfigFile()
        self._description = None

    def _append_reflog(self, *args):
        self._reflog.append(args)

    def set_description(self, description):
        self._description = description

    def get_description(self):
        return self._description

    def _determine_file_mode(self):
        """Probe the file-system to determine whether permissions can be trusted.

        Returns: True if permissions can be trusted, False otherwise.
        """
        return sys.platform != "win32"

    def _put_named_file(self, path, contents):
        """Write a file to the control dir with the given name and contents.

        Args:
          path: The path to the file, relative to the control dir.
          contents: A string to write to the file.
        """
        self._named_files[path] = contents

    def _del_named_file(self, path):
        try:
            del self._named_files[path]
        except KeyError:
            pass

    def get_named_file(self, path, basedir=None):
        """Get a file from the control dir with a specific name.

        Although the filename should be interpreted as a filename relative to
        the control dir in a disk-baked Repo, the object returned need not be
        pointing to a file in that location.

        Args:
          path: The path to the file, relative to the control dir.
        Returns: An open file object, or None if the file does not exist.
        """
        contents = self._named_files.get(path, None)
        if contents is None:
            return None
        return BytesIO(contents)

    def open_index(self):
        """Fail to open index for this repo, since it is bare.

        Raises:
          NoIndexPresent: Raised when no index is present
        """
        raise NoIndexPresent()

    def get_config(self):
        """Retrieve the config object.

        Returns: `ConfigFile` object.
        """
        return self._config

    @classmethod
    def init_bare(cls, objects, refs):
        """Create a new bare repository in memory.

        Args:
          objects: Objects for the new repository,
            as iterable
          refs: Refs as dictionary, mapping names
            to object SHA1s
        """
        ret = cls()
        for obj in objects:
            ret.object_store.add_object(obj)
        for refname, sha in refs.items():
            ret.refs.add_if_new(refname, sha)
        ret._init_files(bare=True)
        return ret
