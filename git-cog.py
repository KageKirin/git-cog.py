#!/usr/local/bin/python3

import os
import sys
import re
import string
from pygit2 import Repository
import giturlparse
import argparse

repo = Repository('.')

def parseArgs_create_pullrequest(args_tail):
    parser = argparse.ArgumentParser('git cog create-pullrequest <origin>')
    parser.add_argument('--into', help='base branch to merge into', type=str, default="master")
    parser.add_argument('--head', help='branch to merge', type=str, default=repo.head.shorthand)
    parser.add_argument('-t', '--title', help='title', type=str, default='merge {}'.format(repo.head.shorthand))
    parser.add_argument('-m', '--message', help='message', type=str, default='merging {}'.format(repo.head.shorthand))
    subargs = parser.parse_args(args_tail)
    return subargs

def parseArgs_find_pullrequest(args_tail):
    parser = argparse.ArgumentParser('git cog find-pullrequest <origin>')
    parser.add_argument('--into', help='base branch to merge into', type=str, default="master")
    parser.add_argument('--head', help='branch to merge', type=str, default=repo.head.shorthand)
    subargs = parser.parse_args(args_tail)
    return subargs

def parseArgs_help(action, args_tail):
    action = re.sub('-', '_', action)
    actions = {
        'create_pullrequest': parseArgs_create_pullrequest,
        'find_pullrequest': parseArgs_find_pullrequest
    }
    fn = actions.get(action)
    assert fn, "Invalid action {}".format(action)
    fn(['--help'])



class GithubCog:
    def __init__(self, baseurl, repopath, token):
        from github import Github
        self.url_http = 'https://{}/{}'.format(baseurl, repopath)
        self.url_api = 'https://{}/api/v3'.format(baseurl)
        self.repo = repopath
        self.handle = Github(base_url=self.url_api, login_or_token=token)
        assert self.handle, "could not connect to server at {}".format(self.url_api)
        self.repo_handle = self.handle.get_repo(self.repo)
        assert self.repo_handle, "could not retrieve repo at {}".format(self.url_http)

    def create_pullrequest(self, args_tail):
        args = parseArgs_create_pullrequest(args_tail)
        pr_handle = self.repo_handle.create_pull(
            title=args.title,
            body=args.message,
            base=args.into,
            head=args.head,
            maintainer_can_modify=True)
        assert pr_handle, "could not create pull request"
        print("created pull request:", pr_handle.html_url)
        return pr_handle.html_url

    def find_pullrequest(self, args_tail):
        args = parseArgs_find_pullrequest(args_tail)
        prs = self.repo_handle.get_pulls(
            base=args.into,
            head=args.head)
        #print("found {} pull requests".format(len(prs)))
        for pr in prs:
            print(pr.html_url, '\t', pr.title, pr.merged, pr.merged_at, pr.merge_commit_sha)

    def find_pullrequests(self, args_tail):
        return self.find_pullrequest(args_tail)

    ## must come last
    def get_action(self, action):
        return getattr(self, action, None)




class GitlabCog:
    def __init__(self, baseurl, repopath, token):
        from gitlab import Gitlab
        self.url_http = 'https://{}/{}'.format(baseurl, repopath)
        self.url_api = 'https://{}'.format(baseurl)
        self.repo = repopath
        self.handle = Gitlab(self.url_api, private_token=token)
        assert self.handle, "could not connect to server at {}".format(self.url_api)
        authOk = self.handle.auth()
        assert authOk, "could not authenticate with server at {}".format(self.url_api)
        print(self.repo)
        self.repo_handle = self.projects.get(self.repo)
        assert self.repo_handle, "could not retrieve repo at {}".format(self.url_http)

    def create_pullrequest(self, args_tail):
        args = parseArgs_create_pullrequest(args_tail)
        pr_handle = self.repo_handle.mergerequests.create({
            'title': args.title,
            'description': args.message,
            'target_branch': args.into,
            'source_branch': args.head,
        })
        assert pr_handle, "could not create merge request"
        print("created pull request:", pr_handle.web_url)
        return pr_handle.web_url

    def find_pullrequest(self, args_tail):
        args = parseArgs_find_pullrequest(args_tail)
        prs = self.repo_handle.mergerequests.list({
            'target_branch': args.into,
            'source_branch': args.head,
        })
        #print("found {} pull requests".format(len(prs)))
        for pr in prs:
            print(pr.web_url, '\t', pr.title, pr.merged, pr.merged_at, pr.merge_commit_sha)

    def find_pullrequests(self, args_tail):
        return self.find_pullrequest(args_tail)

    ## must come last
    def get_action(self, action):
        return getattr(self, action, None)


###----

def main(args):
    remo = repo.remotes[args.remote]
    url = giturlparse.parse(remo.url)
    url_domain = '{}/{}'.format(url.owner, url.name)

    tokens = list(map(lambda t: t.value, filter(lambda h: h.name == 'cog.'+url.resource+'.token', repo.config.__iter__())))
    apis = list(map(lambda t: t.value, filter(lambda h: h.name == 'cog.'+url.resource+'.api', repo.config.__iter__())))

    assert len(tokens) > 0, "no token found for {}".format(url.resource)
    assert len(apis) > 0, "no api specified for {}".format(url.resource)
    api = apis[0]

    cog = None
    for token in tokens:
        if api == 'github':
            cog = GithubCog(url.resource, url_domain, token)
        elif api == 'gitlab':
            cog = GitlabCog(url.resource, url_domain, token)
        if cog:
            break
    
    assert cog, "no API cog found for {}".format(url.resource)

    action = cog.get_action(args.action)
    assert action, "{} is not a defined action".format(args.action)
    action(args.tail)

###----

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', help='action to take on remote', type=str)
    parser.add_argument('remote', help='git remote to use', type=str)
    parser.add_argument('tail', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    
    args.action = re.sub('-', '_', args.action)
    if args.action == 'help':
        parseArgs_help(args.remote, args.tail)
    main(args)

###----
