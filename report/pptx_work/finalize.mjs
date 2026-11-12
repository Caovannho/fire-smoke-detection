import path from 'node:path';
import {pathToFileURL} from 'node:url';
import fs from 'node:fs/promises';
// The managed Windows workspace disallows hard links. Preserve exclusive publish semantics.
const originalLink=fs.link.bind(fs);
fs.link=async(a,b)=>{try{return await originalLink(a,b);}catch(e){if(e.code!=='EPERM')throw e;return fs.copyFile(a,b,1);}};
const skill='C:/Users/PC/.codex/plugins/cache/openai-primary-runtime/presentations/26.1105.12137/skills/presentations';
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
try{
const result=await finalizePresentation({workspaceDir:path.resolve('.'),candidatePath:path.resolve('report/pptx_work/candidate.pptx'),finalPath:path.resolve('report/output/DoAn_PhatHienChayKhoi_NangCap_22Slide.pptx'),pythonExecutable:'C:/Program Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1105-1297-0_26.1105.1297.0_x64__3k8sg7r9htsxt/dependencies/python/python.exe',integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','18288000,10287000','--validate-bullet-geometry','--validate-heading-fit',...[13,14,19,21].flatMap(n=>['--require-native-table-slide',String(n)])],explicitTotalSlideCount:22,requiredNativeTableOwnerSlides:[13,14,19,21],requiredNativeChartOwnerSlides:[],verifyArtifactToolImport:true,receiptPath:path.resolve('report/pptx_work/validation.json')});
console.log(JSON.stringify(result));
}catch(e){console.error(e.message);console.error(JSON.stringify(e.report??e,null,2));process.exitCode=1;}

