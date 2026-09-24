"""Build an isolated copy of current app sources and tests; never run Git or the live app."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile

ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'Evaluation/iOS27/safeguards'
WORK=RUN/'build'
s=importlib.util.spec_from_file_location('base',ROOT/'scripts/ios27-evaluation/run.py')
c=importlib.util.module_from_spec(s);s.loader.exec_module(c)


def openstep(value):
    if isinstance(value,dict):return '{\n'+''.join(f'{json.dumps(k)} = {openstep(v)};\n' for k,v in value.items())+'}'
    if isinstance(value,list):return '('+','.join(openstep(v) for v in value)+')'
    return json.dumps(str(value))


def main():
    c.require(os.environ.get('SPI_BUILDER')!='1','Remote documentation dependencies forbidden')
    c.require(not (RUN/'manifest.json').exists(),'Already prepared; preserve frozen sources')
    free=shutil.disk_usage(ROOT).free
    size=sum(p.stat().st_size for p in (ROOT/'Evaluation/iOS27').rglob('*') if p.is_file())
    c.require(free-2*1024**3>=10*1024**3 and size+2*1024**3<8*1024**3,'Build reserve unavailable')
    WORK.mkdir(parents=True,exist_ok=True)
    resolved=ROOT/'Remember/Remember.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved'
    pin=c.read(resolved)['pins'][0]
    c.require(pin['identity']=='grdb.swift' and pin['state']['version']=='7.11.1','Unexpected dependency pin')
    revision=pin['state']['revision']
    url=f'https://codeload.github.com/groue/GRDB.swift/tar.gz/{revision}'
    archive=WORK/'grdb.tar.gz'
    if not archive.exists():
        # System curl uses the system trust store; do not disable TLS validation.
        data=subprocess.check_output(['/usr/bin/curl','--fail','--location','--proto','=https',
            '--max-time','60','--max-filesize',str(40*1024**2),url],timeout=70)
        c.require(len(data)<=40*1024**2,'Dependency archive too large')
        with archive.open('xb') as stream:stream.write(data)
    package=WORK/f'GRDB.swift-{revision}'
    if not package.exists():
        with tarfile.open(archive) as bundle:
            for member in bundle.getmembers():
                path=(WORK/member.name).resolve()
                c.require(path.is_relative_to(package.resolve()) and not member.islnk(),'Unsafe archive member')
                if member.issym():
                    c.require((path.parent/member.linkname).resolve().is_relative_to(package.resolve()),'Escaping archive symlink')
            bundle.extractall(WORK,filter='data')
    c.publish(RUN/'dependency.json',{'url':url,'revision':revision,'version':'7.11.1','archiveSHA256':c.digest(archive),
        'packageResolvedSHA256':c.digest(resolved),'gitUsed':False,'dependencyUpgrade':False})
    app=WORK/'Remember';tests=WORK/'RememberTests'
    c.require(not app.exists() and not tests.exists(),'Partial prepared source tree; preserve and inspect')
    shutil.copytree(ROOT/'Remember/Remember',app)
    shutil.copytree(ROOT/'Remember/Shared',WORK/'Shared')
    # Replace only this probe-owned entry point; production remains byte-for-byte unchanged.
    (app/'RememberApp.swift').write_text('import SwiftUI\n@main struct RememberApp: App { var body: some Scene { WindowGroup { Text("Isolated organizer safeguards — fictional stores only") } } }\n')
    tests.mkdir()
    for name in ['D3OrganizationTests.swift','SentenceModelRecoveryTests.swift']:
        shutil.copy2(ROOT/'Remember/RememberTests'/name,tests/name)
    shutil.copy2(Path(__file__).with_name('AdditionalSafeguards.swift'),tests/'AdditionalSafeguards.swift')
    original=ROOT/'Remember/Remember.xcodeproj/project.pbxproj'
    project=json.loads(subprocess.check_output(['plutil','-convert','json','-o','-',str(original)],text=True))
    objects=project['objects'];project_node=objects[project['rootObject']]
    ids={node.get('name'):key for key,node in objects.items() if node.get('isa')=='PBXNativeTarget'}
    app_id=ids['Remember'];test_id=ids['RememberTests']
    project_node['targets']=[app_id,test_id]
    project_node.get('attributes',{}).pop('TargetAttributes',None)
    for node in objects.values():
        if node.get('isa')=='XCRemoteSwiftPackageReference':
            node.clear();node.update(isa='XCLocalSwiftPackageReference',relativePath=str(package))
        if node.get('isa')=='XCBuildConfiguration':
            settings=node.get('buildSettings',{})
            for key in ['CODE_SIGN_ENTITLEMENTS','INFOPLIST_FILE','ASSETCATALOG_COMPILER_APPICON_NAME','ASSETCATALOG_COMPILER_GLOBAL_ACCENT_COLOR_NAME']:
                settings.pop(key,None)
            if 'PRODUCT_BUNDLE_IDENTIFIER' in settings:
                settings['PRODUCT_BUNDLE_IDENTIFIER']='SimpleStudio.Remember.Stage1Safety'+('.Tests' if 'Tests' in settings['PRODUCT_BUNDLE_IDENTIFIER'] else '')
            settings.update(GENERATE_INFOPLIST_FILE='YES',ENABLE_TESTABILITY='YES',SWIFT_OPTIMIZATION_LEVEL='-Onone',
                COMPILER_INDEX_STORE_ENABLE='NO',ENABLE_PREVIEWS='NO')
    objects[app_id]['dependencies']=[]
    objects[app_id]['buildPhases']=[key for key in objects[app_id]['buildPhases'] if objects[key]['isa']!='PBXCopyFilesBuildPhase']
    # Test target directly imports GRDB for append-only trigger verification.
    objects[test_id]['packageProductDependencies']=objects[app_id].get('packageProductDependencies',[])
    app_framework=next(objects[k] for k in objects[app_id]['buildPhases'] if objects[k]['isa']=='PBXFrameworksBuildPhase')
    test_framework=next(objects[k] for k in objects[test_id]['buildPhases'] if objects[k]['isa']=='PBXFrameworksBuildPhase')
    test_framework['files']=app_framework['files']
    project_dir=WORK/'Remember.xcodeproj';project_dir.mkdir()
    (project_dir/'project.pbxproj').write_text('// !$*UTF8*$!\n'+openstep(project)+'\n')
    schemes=project_dir/'xcshareddata/xcschemes';schemes.mkdir(parents=True)
    def ref(identifier,name):return f'<BuildableReference BuildableIdentifier="primary" BlueprintIdentifier="{identifier}" BuildableName="{name}" BlueprintName="{name.split(".")[0]}" ReferencedContainer="container:Remember.xcodeproj"/>'
    scheme=f'''<?xml version="1.0" encoding="UTF-8"?>
<Scheme LastUpgradeVersion="2700" version="1.3">
<BuildAction parallelizeBuildables="YES" buildImplicitDependencies="YES"><BuildActionEntries><BuildActionEntry buildForTesting="YES" buildForRunning="YES" buildForProfiling="NO" buildForArchiving="NO" buildForAnalyzing="YES">{ref(app_id,'Remember.app')}</BuildActionEntry></BuildActionEntries></BuildAction>
<TestAction buildConfiguration="Debug" selectedDebuggerIdentifier="Xcode.DebuggerFoundation.Debugger.LLDB" selectedLauncherIdentifier="Xcode.IDEFoundation.Launcher.LLDB" shouldUseLaunchSchemeArgsEnv="YES"><Testables><TestableReference skipped="NO" parallelizable="NO">{ref(test_id,'RememberTests.xctest')}</TestableReference></Testables></TestAction>
</Scheme>'''
    (schemes/'Safeguards.xcscheme').write_text(scheme)
    source_paths=list((ROOT/'Remember/Remember').rglob('*'))+list((ROOT/'Remember/Shared').rglob('*'))
    source_paths += [original,resolved]+list(Path(__file__).parent.glob('*'))+[ROOT/'Remember/RememberTests'/n for n in ['D3OrganizationTests.swift','SentenceModelRecoveryTests.swift']]
    c.publish(RUN/'manifest.json',{'sources':{str(p.relative_to(ROOT)):c.digest(p) for p in source_paths if p.is_file()},
        'generated':{str(p.relative_to(RUN)):c.digest(p) for folder in [app,tests,WORK/'Shared',project_dir] for p in folder.rglob('*') if p.is_file()},
        'dependencyFiles':{str(p.relative_to(WORK)):c.digest(p) for p in package.rglob('*') if p.is_file()},
        'bundle':'SimpleStudio.Remember.Stage1Safety','productionChanged':False,'isolatedEntryPoint':True})
    print(json.dumps({'prepared':True,'project':str(project_dir),'tests':23}))


if __name__=='__main__':main()
