import argparse
import collections
import configparser
import hashlib
import os
import re
import sys
import zlib

argparser              = argparse.ArgumentParser(description="git alternative but it's zz")
argsubparsers          = argparser.add_subparsers(title="Commands", dest="command")
argsubparsers.required = True

argsp                  = argsubparsers.add_parser("init", help="Initialize a new, empty repository.")
argsp.add_argument("path",
                    metavar="directory",
                    nargs="?",
                    default=".",
                    help="Where to create the repository.")

class GitObject(object):
    repo = None

    def __init__(self, repo, data=None):
        self.repo = repo

        if data != None:
            self.deserialize(data)

    # TODO
    def serialize(self):
        raise Exception("Unimplemented")

    # TODO
    def deserialize(self, data):
        raise Exception("Unimplemented")

class GitRepository(object):
    """ A git repository """

    worktree = None
    gitdir   = None
    conf     = None

    def __init__(self, path, force=False):
        self.worktree = path
        self.gitdir   = os.path.join(path, ".git")

        if not (force or os.path.isdir(self.gitdir)):
            raise Exception(f"Not a git repository {path}")

        # Read config file in .git/config
        self.conf = configparser.ConfigParser()
        cf        = repo_file(self, "config")

        if cf and os.path.exists(cf):
            self.conf.read([cf])
        elif not force:
            raise Exception("Configuration file missing")

        if not force:
            vers = int(self.conf.get("core", "repositoryformatversion"))
            if vers != 0:
                raise Exception(f"Unsupported repositoryformatversion {vers}")


def repo_path(repo, *path):
    """ Compute path under repo's gitdir """
    return os.path.join(repo.gitdir, *path)

def repo_dir(repo, *path, mkdir=False):
    """ Same as repo_path, but mkdir *path if absent if mkdir. """
    path = repo_path(repo, *path)

    if os.path.exists(path):
        if (os.path.isdir(path)):
            return path
        else:
            raise Exception(f"Not a directory {path}")

    if mkdir:
        os.makedirs(path)
        return path
    else:
        return None

def repo_file(repo, *path, mkdir=False):
    """ Same as repo_path, but create dirname(*path) if absent. """
    if repo_dir(repo, *path[:-1], mkdir=mkdir):
        return repo_path(repo, *path)

def repo_create(path):
    """ Create a new repo at path. """
    repo = GitRepository(path, True)

    # First we make sure the path either doesn't exists or is
    # an empty dir.

    if os.path.exists(repo.worktree):
        if not os.path.isdir(repo.worktree):
            raise Exception(f"{path} is not a directory!")
        if os.listdir(repo.worktree):
            raise Exception(f"{path} is not empty!")
    else:
        os.makedirs(repo.worktree)

    assert(repo_dir(repo, "branches", mkdir=True))
    assert(repo_dir(repo, "objects", mkdir=True))
    assert(repo_dir(repo, "refs", "tags", mkdir=True))
    assert(repo_dir(repo, "refs", "heads", mkdir=True))

    # .git/description
    with open(repo_file(repo, "description"), "w") as f:
        f.write("Unnamed repository: edit this file 'description to name the repository.\n")

    #.git/HEAD
    with open(repo_file(repo, "HEAD"), "w") as f:
        f.write("ref: refs/heads/master\n")

    with open(repo_file(repo, "config"), "w") as f:
        config = repo_default_config()
        config.write(f)

    return repo

def repo_default_config():
    ret = configparser.ConfigParser()

    ret.add_section("core")
    ret.set("core", "repositoryformatversion", "0")
    ret.set("core", "filemode", "false")
    ret.set("core", "bare", "false")

    return ret

def repo_find(path=".", required=True):
    path = os.path.realpath(path)

    if os.path.isdir(os.path.join(path, ".git")):
        return GitRepository(path)

    # If we haven't returned, recurse in parent, if w
    parent = os.path.realpath(os.path.join(path, ".."))

    if parent == path:
        # Bottom case
        if required:
            raise Exception("No git directory.")
        else:
            return None

        return repo_find(parent, required)

def cmd_init(args):
    repo_create(args.path)

def main(argv=sys.argv[1:]):
    args = argparser.parse_args(argv)

    if   args.command == "add"          : cmd_add(args)
    elif args.command == "cat-file"     : cmd_cat_file(args)
    elif args.command == "checkout"     : cmd_checkout(args)
    elif args.command == "commit"       : cmd_commit(args)
    elif args.command == "hash-object"  : cmd_hash_oject(args)
    elif args.command == "init"         : cmd_init(args)
    elif args.command == "log"          : cmd_log(args)
    elif args.command == "ls-tree"      : cmd_ls_tree(args)
    elif args.command == "merge"        : cmd_merge(args)
    elif args.command == "rebase"       : cmd_rebase(args)
    elif args.command == "rev-parse"    : cmd_rev_parse(args)
    elif args.command == "rm"           : cmd_rm(args)
    elif args.command == "show-ref"     : cmd_show_ref(args)
    elif args.command == "tag"          : cmd_tag(args)
