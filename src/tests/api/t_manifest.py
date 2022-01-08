#!/usr/bin/python3.5
# -*- coding: utf-8 -*-
#
# CDDL HEADER START
#
# The contents of this file are subject to the terms of the
# Common Development and Distribution License (the "License").
# You may not use this file except in compliance with the License.
#
# You can obtain a copy of the license at usr/src/OPENSOLARIS.LICENSE
# or http://www.opensolaris.org/os/licensing.
# See the License for the specific language governing permissions
# and limitations under the License.
#
# When distributing Covered Code, include this CDDL HEADER in each
# file and include the License file at usr/src/OPENSOLARIS.LICENSE.
# If applicable, add the following below this CDDL HEADER, with the
# fields enclosed by brackets "[]" replaced with your own identifying
# information: Portions Copyright [yyyy] [name of copyright owner]
#
# CDDL HEADER END
#

# Copyright (c) 2008, 2017, Oracle and/or its affiliates. All rights reserved.

from . import testutils
if __name__ == "__main__":
        testutils.setup_environment("../../../proto")
import pkg5unittest

import unittest
import tempfile
import os
import six
import sys
import types
import itertools

import pkg as pkg
import pkg.actions as actions
import pkg.client.api_errors as api_errors
import pkg.digest as digest
import pkg.fmri as fmri
import pkg.manifest as manifest
import pkg.misc as misc
import pkg.portable as portable
import pkg.facet as facet
import pkg.variant as variant

class TestManifest(pkg5unittest.Pkg5TestCase):

        def setUp(self):
                pkg5unittest.Pkg5TestCase.setUp(self)

                self.m1 = manifest.Manifest()
                self.m1_contents = """\
set com.sun,test=true
depend type=require fmri=pkg:/library/libc
file fff555fff mode=0555 owner=sch group=staff path=/usr/bin/i386/sort isa=i386
"""
                self.m2 = manifest.Manifest()
                self.m2_contents = """\
set com.sun,test=false
set com.sun,data=true
depend type=require fmri=pkg:/library/libc
file fff555ff9 mode=0555 owner=sch group=staff \\
 path=/usr/bin/i386/sort isa=i386
file eeeaaaeee mode=0555 owner=sch group=staff path=/usr/bin/amd64/sort isa=amd64

file ff555fff mode=0555 owner=root group=bin path=/kernel/drv/foo isa=i386
file ff555ffe mode=0555 owner=root group=bin path=/kernel/drv/amd64/foo isa=amd64
file ff555ffd mode=0644 owner=root group=bin path=/kernel/drv/foo.conf
"""

                self.m2_signatures = {
                    "sha-1": "7272cb2461a8a4ccf958b7a7f13f3ae20cbb0212"
                }

                #
                # Try to keep this up to date with one of
                # every action type.
                #
                self.diverse_contents = """\
set com.sun,test=false
set name=pkg.description value="The Z Shell (zsh) is a Bourne-like shell " \\
    "designed for interactive use, although it is also a powerful scripting " \\
    "language.  Many of the useful features of bash, ksh, and tcsh were " \\
    "incorporated into zsh, but many original features were added."
depend type=require fmri=pkg:/library/libc
file fff555ff9 mode=0555 owner=sch group=staff path=/usr/bin/i386/sort isa=i386
dir owner=root path=usr/bin group=bin mode=0755 variant.arch=i386 variant.arch=sparc
dir owner=root path="opt/dir with spaces in value" group=bin mode=0755
dir owner=root path="opt/dir with " \\
    "whitespaces        " \\
    "in value" group=bin mode=0755
link path=usr/lib/amd64/libjpeg.so \\
target=libjpeg.so.62.0.0
hardlink path=usr/bin/amd64/rksh93 target=ksh93 variant.opensolaris.zone=global
group groupname=testgroup gid=10
"""

                self.m4_contents = """\
set com.sun,test=false
set com.sun,data=true
depend type=require fmri=pkg:/library/libc
file fff555ff9 mode=0555 owner=sch group=staff path=/usr/bin/i386/sort \\
isa=i386
"""

                self.m5_contents = """\
set com.sun,test=false
set com.sun,data=true
depend type=optional fmri=pkg:/library/libc
file fff555ff9 mode=0555 owner=sch group=staff path=/usr/bin/i386/sort isa=i386
"""

        def test_set_content1(self):
                """ ASSERT: manifest string repr reflects its construction """

                self.m1.set_content(self.m1_contents)

                # It would be nice if we could just see if the string
                # representation of the manifest matched the input, but the
                # order of individual fields seems to change.  Instead we look
                # for useful substrings.

                # Index raises an exception if the substring isn't found;
                # if that were to happen, the test case would then fail.
                mstr = str(self.m1)
                mstr.index("fmri=pkg:/library/libc")
                mstr.index("owner=sch")
                mstr.index("group=staff")
                mstr.index("isa=i386")

                # Verify set_content with a byte string with unicode data
                # works.
                bstr = "set name=pkg.summary:th value=\"ซอฟต์แวร์ \""
                m = manifest.Manifest()
                m.set_content(bstr)
                output = list(m.as_lines())[0].rstrip()
                self.assertEqual(bstr, output)
                self.assertTrue(isinstance(output, str))

                # Verify set_content with a Unicode string works.
                m = manifest.Manifest()
                if six.PY2:
                        m.set_content(six.text_type(bstr, "utf-8"))
                else:
                        m.set_content(bstr)
                output = list(m.as_lines())[0].rstrip()
                self.assertEqual(bstr, output)
                self.assertTrue(isinstance(output, str))

                # Verify Manifests using line continuation '\' are parsed as
                # expected.
                m = manifest.Manifest()
                m.set_content(self.diverse_contents)
                expected = sorted('''\
set name=com.sun,test value=false
set name=pkg.description value="The Z Shell (zsh) is a Bourne-like shell designed for interactive use, although it is also a powerful scripting language.  Many of the useful features of bash, ksh, and tcsh were incorporated into zsh, but many original features were added."
depend fmri=pkg:/library/libc type=require
group gid=10 groupname=testgroup
dir group=bin mode=0755 owner=root path="opt/dir with spaces in value"
dir group=bin mode=0755 owner=root path="opt/dir with whitespaces        in value"
dir group=bin mode=0755 owner=root path=usr/bin variant.arch=i386 variant.arch=sparc
file fff555ff9 group=staff isa=i386 mode=0555 owner=sch path=usr/bin/i386/sort
hardlink path=usr/bin/amd64/rksh93 target=ksh93 variant.opensolaris.zone=global
link path=usr/lib/amd64/libjpeg.so target=libjpeg.so.62.0.0
'''.splitlines())
                actual = sorted(l.strip() for l in m.as_lines())

                self.assertEqualDiff(expected, actual)

        def test_diffs1(self):
                """ humanized_differences runs to completion """

                # humanized_differences is for now, at least, just a
                # useful diagnostic
                self.m1.set_content(self.m1_contents)
                self.m2.set_content(self.m2_contents)
                self.m2.humanized_differences(self.m1)
                
        def test_diffs2(self):
                self.m1.set_content(self.m1_contents)
                self.m2.set_content(self.m2_contents)
                diffs = self.m2.combined_difference(self.m1)

        #
        # Do the most obvious thing: build two manifests
        # from the same string, and then diff the results
        #
        def test_diffs3(self):
                """ ASSERT: building m1(c) and m2(c) should yield no diffs """
                self.m1.set_content(self.diverse_contents)
                self.m2.set_content(self.diverse_contents)

                diffs = self.m2.combined_difference(self.m1)
                self.assertEqual(len(diffs), 0)

                diffs = self.m1.combined_difference(self.m2)
                self.assertEqual(len(diffs), 0)
                
        def test_diffs4(self):
                """ ASSERT: Building m' from diff(m, null) should yield m """

                self.m2.set_content(self.m2_contents)
                diffs = self.m2.combined_difference(manifest.null)

                new_contents = ""
                for d in diffs:
                        new_contents += str(d[1]) + "\n"

                mtmp = manifest.Manifest()
                #print(new_contents)
                mtmp.set_content(new_contents)

                diffs = self.m2.combined_difference(mtmp)
                self.assertEqual(len(diffs), 0)

        def test_diffs5(self):
                """ detect an attribute change """

                self.m1.set_content(self.m4_contents)
                self.m2.set_content(self.m5_contents)

                #print(self.m2.display_differences(self.m1))

                diffs = self.m2.combined_difference(self.m1)
                self.assertEqual(len(diffs), 1)

        def test_diffs6(self):
                """ ASSERT: changes in action work """

                self.m1.set_content(
                    "dir mode=0755 owner=root group=sys path=/bin/foo")
                self.m2.set_content(
                    "file 12345 mode=0755 owner=root group=sys path=/bin")

                diffs = self.m2.combined_difference(self.m1)
                #
                # Expect to see a directory going away, and a file being
                # added
                #
                for d in diffs:
                        if type(d[0]) == type(None):
                                self.assertEqual(type(d[1]),
                                    pkg.actions.file.FileAction)
                        if type(d[1]) == type(None):
                                self.assertEqual(type(d[0]),
                                    pkg.actions.directory.DirectoryAction)

                self.assertEqual(len(diffs), 2)

        def test_diffs7(self):
                """ ASSERT: changes in attributes are detected """

                self.m1.set_content("""
            dir mode=0755 owner=root group=sys path=bin
            dir mode=0755 owner=root group=sys path=bin/foo
            file 00000000 mode=0644 owner=root group=sys path=a
            link path=bin/change-link target=change variant.opensolaris.zone=global
                    """)

                self.m2.set_content("""
            dir mode=0755 owner=root group=sys path=bin
            dir mode=0555 owner=root group=sys path=bin/foo
            file 00000000 mode=0444 owner=root group=sys path=a
            link path=bin/change-link target=change variant.opensolaris.zone=nonglobal
                    """)

                diffs = self.m2.combined_difference(self.m1)
                #
                # Expect to see a directory -> directory, file -> file, etc.
                # 3 of the 4 things above should have changed.
                #
                self.assertEqual(len(diffs), 3)
                for d in diffs:
                        self.assertEqual(type(d[0]), type(d[1]))


        def test_diffs8(self):
                """ ASSERT: changes in checksum are detected """

                self.m1.set_content("""
                    file 00000000 mode=0444 owner=root group=sys path=a
                    file 00000001 mode=0444 owner=root group=sys path=b
                    """)
                self.m2.set_content("""
                    file 00000000 mode=0444 owner=root group=sys path=a
                    file 00000002 mode=0444 owner=root group=sys path=b
                    """)

                diffs = self.m2.combined_difference(self.m1)
                #
                # Expect to see b change.
                #
                self.assertEqual(len(diffs), 1)
                for d in diffs:
                        self.assertEqual(type(d[0]), type(d[1]))
                        self.assertEqual(d[0].attrs["path"], "b")

        def test_diffs9(self):
                """ ASSERT: addition and removal are detected """

                self.m1.set_content(self.diverse_contents)
                self.m2.set_content("")

                diffs = self.m2.combined_difference(self.m1)
                diffs2 = self.m1.combined_difference(self.m2)

                #
                # Expect to see something -> None differences
                #
                self.assertEqual(len(diffs), 10)
                for d in diffs:
                        self.assertEqual(type(d[1]), type(None))

                #
                # Expect to see None -> something differences
                #
                self.assertEqual(len(diffs2), 10)
                for d in diffs2:
                        self.assertEqual(type(d[0]), type(None))
                        self.assertNotEqual(type(d[1]), type(None))

        def test_diffs10(self):
                """ ASSERT: changes in target are detected """

                self.m1.set_content("""
                    link target=old path=a
                    hardlink target=old path=b
                    """)
                self.m2.set_content("""
                    link target=new path=a
                    hardlink target=new path=b
                    """)

                diffs = self.m2.combined_difference(self.m1)
                #
                # Expect to see differences in which "target" flips from "old"
                # to "new"
                #
                self.assertEqual(len(diffs), 2)
                for d in diffs:
                        self.assertEqual(type(d[0]), type(d[1]))
                        self.assertEqual(d[0].attrs["target"], "old")
                        self.assertEqual(d[1].attrs["target"], "new")


        def test_dups1(self):
                """ Test the duplicate search.  /bin shouldn't show up, since
                    they're identical actions, but /usr should show up three
                    times."""

                # XXX dp: "duplicates" is an odd name for this routine.

                self.m1.set_content("""\
dir mode=0755 owner=root group=sys path=bin
dir mode=0755 owner=root group=sys path=bin
dir mode=0755 owner=root group=sys path=bin
dir mode=0755 owner=root group=sys path=usr
dir mode=0755 owner=root group=root path=usr
dir mode=0755 owner=bin group=sys path=usr
                        """)

                acount = 0
                for kv, actions in self.m1.duplicates():
                        self.assertEqual(kv, ('dir', 'usr'))
                        for a in actions:
                                acount += 1
                                #print(" {0} {1}".format(kv, a))
                self.assertEqual(acount, 3)

        def test_errors(self):
                """Test that a variety of bogus manifests raise
                InvalidPackageErrors.
                """
                self.assertRaises(api_errors.InvalidPackageErrors,
                    self.m1.set_content, "foobar 1234 owner=root")

                self.assertRaises(api_errors.InvalidPackageErrors,
                    self.m1.set_content, "file 1234 path=foo bar")

                self.assertRaises(api_errors.InvalidPackageErrors,
                    self.m1.set_content, "file 1234 path=\"foo bar")

                self.assertRaises(api_errors.InvalidPackageErrors,
                    self.m1.set_content, "file 1234 =")

        def test_validate(self):
                """Verifies that Manifest validation works as expected."""

                self.m2.set_content(self.m2_contents, signatures=True)
                self.m2.validate(signatures=self.m2_signatures)

                self.m2.set_content(self.diverse_contents, signatures=True)
                self.assertRaises(api_errors.BadManifestSignatures,
                    self.m2.validate, signatures=self.m2_signatures)

                # Verify a manifest that has its content set using a byte string
                # has the same signature as that of one set with a Unicode
                # string when the content is the same.
                bstr = "set name=pkg.summary:th value=\"ซอฟต์แวร์ \""
                m1 = manifest.Manifest()
                m1.set_content(bstr, signatures=True)
                output1 = "".join(m1.as_lines())

                m2 = manifest.Manifest()
                if six.PY2:
                        m2.set_content(six.text_type(bstr, "utf-8"), signatures=True)
                else:
                        m2.set_content(bstr, signatures=True)
                output2 = "".join(m2.as_lines())
                self.assertEqualDiff(output1, output2)
                self.assertEqualDiff(m1.signatures, m2.signatures)


class TestFactoredManifest(pkg5unittest.Pkg5TestCase):

        foo_content = """\
set name=pkg.fmri value=pkg:/foo-content@1.0
dir owner=root path=usr/bin group=bin mode=0755 variant.arch=i386
dir owner=root path="opt/dir with spaces in value" group=bin mode=0755
dir owner=root path="opt/dir with " \\
    "whitespaces   " \\
    "in value" group=bin mode=0755 variant.debug.osnet=true
dir owner=root path=test group=bin mode=0755 facet.test=true
dir owner=root path=vdo group=bin mode=0755 variant.debug.osnet=true \\
    variant.debug.osnet=false
dir owner=root path=vo group=bin mode=0755 variant.osnet=true \\
    variant.osnet=false
dir owner=root path=fdm group=bin mode=0755 facet.debug.multi=true \\
    facet.debug.multi=false
dir owner=root path=fm group=bin mode=0755 facet.multi=true \\
    facet.multi=false
"""

        def setUp(self):
                pkg5unittest.Pkg5TestCase.setUp(self)
                self.cache_dir = tempfile.mkdtemp(dir=self.test_root)
                self.foo_content_p5m = self.make_misc_files(
                    { "foo_content.p5m": self.foo_content })[0]

        def test_cached_gen_actions_by_type(self):
                """Test that when a factored manifest generates actions by type
                from its cached source, it takes the excluded content into
                account."""

                contents = """\
                    set name=pkg.fmri value=pkg:/bar@1
                    set name=variant.foo value=one value=two
                    dir path=one group=sys owner=root variant.foo=one
                    dir path=two group=sys owner=root variant.foo=two
                """
                m1 = manifest.FactoredManifest("bar@1", self.cache_dir,
                    contents=contents)
                self.assertEqual(len(list(m1.gen_actions_by_type("dir"))), 2)
                v = variant.Variants({"variant.foo":"one"})
                m1.exclude_content([v.allow_action, lambda x, publisher: True])
                self.assertEqual(len(list(m1.gen_actions_by_type("dir"))), 1)

        def test_store_to_disk(self):
                """Verfies that a FactoredManifest gets force-loaded before it
                gets stored to disk."""

                m1 = manifest.FactoredManifest("foo-content@1.0", self.cache_dir,
                    pathname=self.foo_content_p5m)

                tmpdir = tempfile.mkdtemp(dir=self.test_root)
                path = os.path.join(tmpdir, "manifest.p5m")
                m1.store(path)
                self.assertEqual(misc.get_data_digest(path,
                    hash_func=digest.DEFAULT_HASH_FUNC),
                    misc.get_data_digest(self.foo_content_p5m,
                    hash_func=digest.DEFAULT_HASH_FUNC))

        def test_get_directories(self):
                """Verifies that get_directories() works as expected."""

                v = variant.Variants({ "variant.arch": "sparc" })
                vexcludes = [v.allow_action, lambda x, publisher: True]

                f = facet.Facets({ "facet.test": False })
                fexcludes = [lambda x, publisher: True, f.allow_action]

                m1 = manifest.FactoredManifest("foo-content@1.0", self.cache_dir,
                    pathname=self.foo_content_p5m)

                all_expected = [
                    "fdm",
                    "fm",
                    "vdo",
                    "vo",
                    "test",
                    "opt/dir with spaces in value",
                    "opt",
                    "usr/bin",
                    "opt/dir with whitespaces   in value",
                    "usr"
                ]

                var_expected = [
                    "fdm",
                    "fm",
                    "opt/dir with spaces in value",
                    "opt",
                    "test"
                ]

                facet_expected = [
                    "vdo",
                    "vo",
                    "opt/dir with spaces in value",
                    "opt",
                    "usr/bin",
                    "opt/dir with whitespaces   in value",
                    "usr"
                ]

                def do_get_dirs():
                        actual = m1.get_directories([])
                        self.assertEqualDiff(sorted(all_expected), sorted(actual))

                        actual = m1.get_directories(vexcludes)
                        self.assertEqualDiff(sorted(var_expected), sorted(actual))

                        actual = m1.get_directories(fexcludes)
                        self.assertEqualDiff(sorted(facet_expected), sorted(actual))

                # Verify get_directories works for initial load.
                do_get_dirs()

                # Now repeat experiment using "cached" FactoredManifest.
                cfile_path = os.path.join(self.cache_dir, "manifest.dircache")
                self.assertTrue(os.path.isfile(cfile_path))
                m1 = manifest.FactoredManifest("foo-content@1.0", self.cache_dir,
                    pathname=self.foo_content_p5m)

                do_get_dirs()

                # Now rewrite the dircache so that it contains actions with
                # paths that are not properly quoted to simulate older, broken
                # behaviour and verify that the cache will be removed and that
                # get_directories() still works as expected.
                m1 = manifest.FactoredManifest("foo-content@1.0", self.cache_dir,
                    pathname=self.foo_content_p5m)

                with open(cfile_path, "w") as f:
                        for a in m1.gen_actions_by_type("dir"):
                                f.write(
                                    "dir path={0} {1}\n".format(a.attrs["path"],
                                        " ".join(
                                            "{0}={1}".format(attr, a.attrs[attr])
                                            for attr in itertools.chain(
                                                *a.get_varcet_keys())
                                        )
                                ))

                # Repeat tests again.
                do_get_dirs()

                # Verify cache file was removed (presumably because we
                # detected it was malformed).
                self.assertTrue(not os.path.exists(cfile_path))

                # Repeat tests again, verifying cache file is recreated.
                m1 = manifest.FactoredManifest("foo-content@1.0", self.cache_dir,
                    pathname=self.foo_content_p5m)
                do_get_dirs()
                self.assertTrue(os.path.isfile(cfile_path))

        def test_clear_cache(self):
                """Verify that FactoredManifest.clear_cache() works as
                expected."""

                # Create FactoredManifest.
                cache_dir = tempfile.mkdtemp(dir=self.test_root)
                m1 = manifest.FactoredManifest("foo-content@1.0", cache_dir,
                    pathname=self.foo_content_p5m)

                # Verify cache was created.
                cfile_path = os.path.join(cache_dir, "manifest.dircache")
                self.assertTrue(os.path.isfile(cfile_path))

                # Create random file in cache_dir.
                rfile_path = os.path.join(cache_dir, "junk")
                self.make_file(rfile_path, "junk")

                # Verify that clear_cache() removes all known files from
                # cache_dir and will not remove directory if unknown are
                # present.
                m1.clear_cache(cache_dir)
                for name in os.listdir(cache_dir):
                        self.assertEqualDiff(name, os.path.basename(rfile_path))

                # Verify that clear_cache() removes cache_dir if empty.
                portable.remove(rfile_path)
                m1.clear_cache(cache_dir)
                self.assertTrue(not os.path.exists(cache_dir))


if __name__ == "__main__":
        unittest.main()

# Vim hints
# vim:ts=8:sw=8:et:fdm=marker
