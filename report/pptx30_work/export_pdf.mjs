import fs from 'node:fs/promises';
import {PresentationFile,FileBlob} from 'file:///C:/Program%20Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1105-1297-0_26.1105.1297.0_x64__3k8sg7r9htsxt/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
const p=await PresentationFile.importPptx(await FileBlob.load('report/output/DoAn_PhatHienChayKhoi_30Slide_HoanChinh.pptx'));
await fs.writeFile('report/output/DoAn_PhatHienChayKhoi_30Slide_HoanChinh.pdf',new Uint8Array(await(await p.export({format:'pdf'})).arrayBuffer()));
console.log('PDF exported',p.slides.items.length);
