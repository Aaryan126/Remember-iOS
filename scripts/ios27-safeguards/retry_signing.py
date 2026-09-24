"""Preserve failed build; generate a separate test project with the app's signing team."""
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess

s=importlib.util.spec_from_file_location('prepare',Path(__file__).with_name('prepare.py'))
p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
c=p.c

def main():
    c.require(c.read(p.RUN/'build-result.json')['returnCode']!=0,'Expected failed original build')
    original=p.WORK/'Remember.xcodeproj'
    destination=p.WORK/'signing-retry'
    c.require(not destination.exists(),'Signing retry already prepared')
    destination.mkdir()
    for name in ['Remember','RememberTests','Shared']:(destination/name).symlink_to(p.WORK/name,target_is_directory=True)
    project=destination/'Remember.xcodeproj';shutil.copytree(original,project)
    node=json.loads(subprocess.check_output(['plutil','-convert','json','-o','-',str(original/'project.pbxproj')],text=True))
    team=re.search(r'DEVELOPMENT_TEAM = ([A-Z0-9]+);',(p.ROOT/'Remember/Remember.xcodeproj/project.pbxproj').read_text())[1]
    for value in node['objects'].values():
        if value.get('isa')=='XCBuildConfiguration':value['buildSettings']['DEVELOPMENT_TEAM']=team
    (project/'project.pbxproj').write_text('// !$*UTF8*$!\n'+p.openstep(node)+'\n')
    c.publish(p.RUN/'signing-retry.json',{'originalBuildSHA256':c.digest(p.RUN/'build-result.json'),
        'originalManifestSHA256':c.digest(p.RUN/'manifest.json'),'launcherSHA256':c.digest(__file__),
        'reason':'Original test target lacked a development team; use the existing app team in isolated project only',
        'generated':{str(file.relative_to(p.RUN)):c.digest(file) for file in project.rglob('*') if file.is_file()}})

if __name__=='__main__':main()
