#!/usr/bin/python

import glob
import os

from setuptools import setup, Extension

MYDIR = os.path.abspath(os.path.dirname(__file__))

try:
    from Cython.Distutils import build_ext

    CYTHON = True
except ImportError:
    CYTHON = False


class BuildFailed(Exception):
    pass


packages = []
environment_variable_value = os.environ.get("SUMMIT_RCM_BLUETOOTH_PLUGIN_EXTRA_PACKAGES", "")
if len(environment_variable_value) > 0:
    extra_packages = [s.strip() for s in environment_variable_value.split()]
else:
    extra_packages = []
for package in extra_packages:
    packages.append(package)


def get_cython_options():
    from distutils.errors import (
        CCompilerError,
        DistutilsExecError,
        DistutilsPlatformError,
    )

    ext_errors = (CCompilerError, DistutilsExecError, DistutilsPlatformError)

    class ve_build_ext(build_ext):
        # This class allows Cython building to fail.

        def run(self):
            try:
                super().run()
            except DistutilsPlatformError:
                raise BuildFailed()

        def build_extension(self, ext):
            try:
                super().build_extension(ext)
            except ext_errors as e:
                raise BuildFailed() from e
            except ValueError as e:
                # this can happen on Windows 64 bit, see Python issue 7511
                if "'path'" in str(e):
                    raise BuildFailed() from e
                raise

    def list_modules(dirname, pattern):
        filenames = glob.glob(os.path.join(dirname, pattern))

        module_names = []
        for name in filenames:
            module, ext = os.path.splitext(os.path.basename(name))
            if module != "__init__":
                module_names.append((module, ext))

        return module_names

    package_names = [p.replace("/", ".") for p in packages]

    modules_to_exclude = []

    cython_package_names = frozenset([])

    ext_modules = [
        Extension(
            package + "." + module,
            [os.path.join(*(package.split(".") + [module + ext]))],
        )
        for package in package_names
        for module, ext in list_modules(
            os.path.join(MYDIR, *package.split(".")),
            ("*.pyx" if package in cython_package_names else "*.py"),
        )
        if (package + "." + module) not in modules_to_exclude
    ]

    for ext_mod in ext_modules:
        ext_mod.cython_directives = {
            "language_level": "3",
            "always_allow_keywords": True,
        }

    cmdclass = {"build_ext": ve_build_ext}
    return cmdclass, ext_modules


def run_setup(CYTHON):
    if CYTHON:
        cmdclass, ext_modules = get_cython_options()
    else:
        cmdclass, ext_modules = {}, []
    setup(
        name="summit-rcm-bluetooth-plugin",
        cmdclass=cmdclass,
        version="1.0",
        packages=packages,
        ext_modules=ext_modules,
    )


def status_msgs(*msgs):
    print("*" * 75, *msgs, "*" * 75, sep="\n")


if not CYTHON:
    run_setup(False)
elif os.environ.get("SUMMIT_RCM_DISABLE_CYTHON"):
    run_setup(False)
    status_msgs(
        "SUMMIT_RCM_DISABLE_CYTHON is set, skipping cython compilation.",
        "Pure-Python build succeeded.",
    )
else:
    try:
        run_setup(True)
    except BuildFailed as exc:
        status_msgs(
            exc.__cause__,
            "Cython compilation could not be completed, speedups are not enabled.",
            "Failure information, if any, is above.",
            "Retrying the build without the C extension now.",
        )

        run_setup(False)

        status_msgs(
            "Cython compilation could not be completed, speedups are not enabled.",
            "Pure-Python build succeeded.",
        )
