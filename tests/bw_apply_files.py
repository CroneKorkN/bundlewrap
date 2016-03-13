# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base64 import b64encode
from os.path import exists, join

from bundlewrap.utils.testing import host_os, make_repo, run


def test_binary_inline_content(tmpdir):
    make_repo(
        tmpdir,
        bundles={
            "test": {
                'files': {
                    join(str(tmpdir), "foo.bin"): {
                        'content_type': 'base64',
                        'content': b64encode("ö".encode('latin-1')),
                    },
                },
            },
        },
        nodes={
            "localhost": {
                'bundles': ["test"],
                'os': host_os(),
            },
        },
    )
    run("bw apply localhost", path=str(tmpdir))
    with open(join(str(tmpdir), "foo.bin"), 'rb') as f:
        content = f.read()
    assert content.decode('latin-1') == "ö"


def test_binary_template_content(tmpdir):
    make_repo(
        tmpdir,
        bundles={
            "test": {
                'files': {
                    join(str(tmpdir), "foo.bin"): {
                        'encoding': 'latin-1',
                    },
                },
            },
        },
        nodes={
            "localhost": {
                'bundles': ["test"],
                'os': host_os(),
            },
        },
    )
    with open(join(str(tmpdir), "bundles", "test", "files", "foo.bin"), 'wb') as f:
        f.write("ö".encode('utf-8'))

    run("bw apply localhost", path=str(tmpdir))
    with open(join(str(tmpdir), "foo.bin"), 'rb') as f:
        content = f.read()
    assert content.decode('latin-1') == "ö"


def test_delete(tmpdir):
    with open(join(str(tmpdir), "foo"), 'w') as f:
        f.write("foo")
    make_repo(
        tmpdir,
        bundles={
            "test": {
                'files': {
                    join(str(tmpdir), "foo"): {
                        'delete': True,
                    },
                },
            },
        },
        nodes={
            "localhost": {
                'bundles': ["test"],
                'os': host_os(),
            },
        },
    )
    run("bw apply localhost", path=str(tmpdir))
    assert not exists(join(str(tmpdir), "foo"))


def test_mako_template_content(tmpdir):
    make_repo(
        tmpdir,
        bundles={
            "test": {
                'files': {
                    join(str(tmpdir), "foo"): {
                        'content_type': 'mako',
                        'content': "${node.name}",
                    },
                },
            },
        },
        nodes={
            "localhost": {
                'bundles': ["test"],
                'os': host_os(),
            },
        },
    )
    run("bw apply localhost", path=str(tmpdir))
    with open(join(str(tmpdir), "foo"), 'rb') as f:
        content = f.read()
    assert content == b"localhost"


def test_mako_template_content_with_secret(tmpdir):
    make_repo(
        tmpdir,
        bundles={
            "test": {
                'files': {
                    join(str(tmpdir), "foo"): {
                        'content_type': 'mako',
                        'content': "${repo.vault.password_for('testing')}",
                    },
                },
            },
        },
        nodes={
            "localhost": {
                'bundles': ["test"],
                'os': host_os(),
            },
        },
    )
    run("bw apply localhost", path=str(tmpdir))
    with open(join(str(tmpdir), "foo"), 'rb') as f:
        content = f.read()
    assert content == b"PBthaaqOXfNOaZVTQpYoUqGJEkSjUrTU"


def test_text_template_content(tmpdir):
    make_repo(
        tmpdir,
        bundles={
            "test": {
                'files': {
                    join(str(tmpdir), "foo"): {
                        'content_type': 'text',
                        'content': "${node.name}",
                    },
                },
            },
        },
        nodes={
            "localhost": {
                'bundles': ["test"],
                'os': host_os(),
            },
        },
    )
    run("bw apply localhost", path=str(tmpdir))
    with open(join(str(tmpdir), "foo"), 'rb') as f:
        content = f.read()
    assert content == b"${node.name}"
