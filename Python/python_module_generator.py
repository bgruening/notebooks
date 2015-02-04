#!/usr/bin/env python
from string import Template

import argparse
parser = argparse.ArgumentParser(description='Parse a python module into a tool_dependencies.xml')
parser.add_argument('module', help='module name on pypi')
parser.add_argument('--version', help='specific version of a module', default='latest')
args = parser.parse_args()

# Find the module on PyPi
try:
    import xmlrpclib
except ImportError:
    import xmlrpc.client as xmlrpclib
client = xmlrpclib.ServerProxy('https://pypi.python.org/pypi')
releases = client.package_releases(args.module)

# No releases usually indicates a capitalisation failure. E.g. pillow vs Pillow.
if len(releases) == 0:
    raise Exception("No releases found. Is the package name correct? (Capitalisation matters)")

# If they want the latest, just grab it.
# TODO: check that sorting is correct and sort with setuputil's version
# comparison method..
if args.version == 'latest':
    args.version = releases[0]

if args.version not in releases:
    raise Exception("Release not listed on PyPi: " + ','.join(releases))

complete_release_information = client.release_data(args.module, args.version)


dependency_list = []
# TODO other deps
# TODO: support more than sdist?
pypi_file_list = client.release_urls(args.module, args.version)
interesting_release = [pypi_file for pypi_file in pypi_file_list if pypi_file['packagetype'] == 'sdist']
dependency_list.append('%(url)s#md5=%(md5_digest)s' % interesting_release[0])


template = Template("""
<?xml version="1.0"?>
<tool_dependency>
    <package name="python" version="2.7">
        <repository name="package_python_2_7" owner="iuc" prior_installation_required="True" />
    </package>
    <package name="$package_name" version="$package_version">
        <install version="1.0">
            <actions>
                <action type="setup_python_environment">
                    <repository name="package_python_2_7" owner="iuc">
                        <package name="python" version="2.7" />
                    </repository>
                    <!-- allow downloading and installing an Python package from https://pypi.org/ -->
$packages
                </action>
            </actions>
        </install>
        <readme><![CDATA[
$readme
]]>
        </readme>
    </package>
</tool_dependency>
""")

content = dict(
            readme=complete_release_information['description'],
            packages='\n'.join([' ' * 20 + '<package>' + x + '</package>' for x in dependency_list]),
            package_name=args.module,
            package_version=args.version,
        )
print template.substitute(content)
