#!/usr/bin/env perl
use strict;
use warnings;
use CPAN::FindDependencies;

my $package_name;
my $complete = 0;
my $quiet = 0;
if(scalar(@ARGV) == 2){
    $package_name = $ARGV[1];
    if($ARGV[0] eq '--complete'){
        $complete = 1;
    }elsif($ARGV[0] eq '--quiet'){
        $quiet = 1;
    }else {
        die "Please invoke with the command: \n\n\tperl $0 [--complete] My::Module::Name;\n\n";
    }
}elsif(scalar(@ARGV) == 1){
    $package_name = $ARGV[0];
}

if(! defined($package_name)){
    die "Please invoke with the command: \n\n\tperl $0 [--complete] My::Module::Name;\n\n";
}

my @deps = CPAN::FindDependencies::finddeps($package_name, perl=>"5.18.1");
# Reverse ordering by depth, and mapped to the distribution url
my @ordered_deps = map {$_->distribution() } sort {$b->depth <=> $a->depth} @deps;

my $template = <<"EOL";
<tool_dependency>
    <package name="perl" version="5.18.1">
        <repository name="package_perl_5_18" owner="iuc" prior_installation_required="True" />
    </package>
    <package name="%s" version="%s">
        <install version="1.0">
            <actions>
                <action type="setup_perl_environment">
                    <repository name="package_perl_5_18" owner="iuc">
                        <package name="perl" version="5.18.1" />
                    </repository>
%s
                </action>
            </actions>
        </install>
        <readme><![CDATA[
            Perl package: %s
        ]]>
        </readme>
    </package>
</tool_dependency>
EOL

my @package_dep_list = map{ " " x 20 . "<package>http://www.cpan.org/authors/id/" . $_ . "</package>"} @ordered_deps;
my $package_deps = join("\n", @package_dep_list);
if($quiet){
    print $package_deps;
    exit 0;
}

# Construct package name from passed value
my $package_pkgname = sprintf("package_perl_%s", lc($package_name));
$package_pkgname =~ s/::/_/g;

# splits P/PE/PEVANS/Scalar-List-Utils-1.41.tar.gz
my @tmp = split(/-/, $deps[0]->distribution);
# Grab 1.41.tar.gz
my $package_pkgversion = $tmp[-1];
# Strip .tar.gz ending
$package_pkgversion =~ s/.tar.gz//g;

my $tool_deps_xml = sprintf($template, $package_pkgname, $package_pkgversion, $package_deps, $package_name);

if(!$complete){
    print $tool_deps_xml;
}else{
    mkdir $package_pkgname;
    open(my $file, '>', "$package_pkgname/tool_dependencies.xml");
    print $file $tool_deps_xml;
    close($file);

    open(my $file2, '>', "$package_pkgname/.shed.yml");
    my $shed_yml_template = <<"EOL";
categories:
- Tool Dependency Packages
description: Contains a tool dependency definition that downloads and compiles all
  dependencies from the Perl %s module.
name: %s
owner: iuc
remote_repository_url: https://github.com/galaxyproject/tools-iuc/tree/master/packages/%s
type: tool_dependency_definition
EOL
    my $shed_yml_str = sprintf($shed_yml_template, $package_name, $package_pkgname, $package_pkgname);
    print $file2 $shed_yml_str;
    close($file2);

}
