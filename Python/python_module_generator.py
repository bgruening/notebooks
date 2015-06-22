#!/usr/bin/env python
import os
import argparse
parser = argparse.ArgumentParser(description='Parse a python module into a tool_dependencies.xml')
parser.add_argument('module', help='module name on pypi')
parser.add_argument('--complete', action='store_true', help='Build the complete folder, .shed.yml and all')
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


template = """
<?xml version="1.0"?>
<tool_dependency>
    <package name="python" version="2.7">
        <repository name="package_python_2_7" owner="iuc" prior_installation_required="True" />
    </package>
    <package name="{package_name}" version="{package_version}">
        <install version="1.0">
            <actions>
                <action type="setup_python_environment">
                    <repository name="package_python_2_7" owner="iuc">
                        <package name="python" version="2.7" />
                    </repository>
{packages}
                </action>
                <action type="set_environment">
                    <environment_variable action="prepend_to" name="PYTHONPATH">$INSTALL_DIR</environment_variable>
                    <environment_variable action="prepend_to" name="PATH">$INSTALL_DIR/bin</environment_variable>
                </action>
            </actions>
        </install>
        <readme><![CDATA[
{readme}
]]>
        </readme>
    </package>
</tool_dependency>
"""

safe_pkg_name = args.module.lower().replace('-', '_')
safe_pkg_vers = args.version.replace('.', '_')

content = dict(
    readme=complete_release_information['description'],
    packages='\n'.join([' ' * 20 + '<package>' + x + '</package>' for x in dependency_list]),
    package_name=safe_pkg_name,
    package_version=args.version,
)

if not args.complete:
    print template.format(**content)
else:
    pkg_dir = 'package_python_2_7_{}_{}'.format(safe_pkg_name, safe_pkg_vers)
    os.makedirs(pkg_dir)

    shed_yml_file = os.path.join(pkg_dir, '.shed.yml')
    tool_dep_file = os.path.join(pkg_dir, 'tool_dependencies.xml')
    with open(shed_yml_file, 'w') as handle:
        shed_template = """categories:
- Tool Dependency Packages
description: Contains a tool dependency definition that downloads and compiles version
  {version} of the python library {module}
name: {pkg_name}
owner: iuc
remote_repository_url: https://github.com/galaxyproject/tools-iuc/tree/master/packages/{pkg_name}
type: tool_dependency_definition"""
        handle.write(shed_template.format(version=args.version,
                                          module=args.module,
                                          pkg_name=pkg_dir))

    with open(tool_dep_file, 'w') as handle:
        handle.write(template.format(**content))
