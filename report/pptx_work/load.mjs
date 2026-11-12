import fs from 'node:fs/promises';
import {PresentationFile,FileBlob} from 'file:///C:/Program%20Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1105-1297-0_26.1105.1297.0_x64__3k8sg7r9htsxt/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
const p=await PresentationFile.importPptx(await FileBlob.load('report/DoAn_PhatHienChayKhoi.pptx.pptx'));
await fs.writeFile('report/pptx_work/source.proto.json',JSON.stringify(p.toProto()));
console.log((await p.inspect({kind:'slide,layout',maxChars:4000})).ndjson);
for(let i=0;i<p.slides.items.length;i++){
 await fs.writeFile(`report/pptx_work/source-${i+1}.png`,new Uint8Array(await (await p.export({slide:p.slides.items[i],format:'png',scale:0.65})).arrayBuffer()));
}
console.log('rendered',p.slides.items.length);

