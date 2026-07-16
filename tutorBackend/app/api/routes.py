import os
import shutil
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse

from app.core.config import (
    FAISS_INDEX_PATH,
    IMAGE_OUTPUT_DIR,
    IMAGE_UPLOAD_DIR,
    PDF_UPLOAD_DIR,
)
from app.rag.chunker import chunk_text
from app.rag.image_captioner import caption_image
from app.rag.image_extractor import extract_images_from_pdf
from app.rag.loader import load_pdf_text
from app.rag.store import build_index, load_index, query_index

router = APIRouter()


@router.get("/ping")
def ping():
    return {"status": "ok", "message": "pong"}


@router.post("/ingest")
async def ingest_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    Path(PDF_UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(IMAGE_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    pdf_path = os.path.join(PDF_UPLOAD_DIR, file.filename)

    with open(pdf_path, "wb") as out_file:
        shutil.copyfileobj(file.file, out_file)

    raw_text = load_pdf_text(pdf_path)
    text_chunks = chunk_text(raw_text)
    text_metadatas = [{"type": "text"} for _ in text_chunks]

    images = extract_images_from_pdf(pdf_path, IMAGE_OUTPUT_DIR)
    image_texts = []
    image_metadatas = []
    caption_results = []

    for image in images:
        try:
            caption = caption_image(image["image_path"])
            caption_results.append({
                "page": image["page"],
                "image_path": image["image_path"],
                "caption": caption,
            })
            if caption:
                image_texts.append(caption)
                image_metadatas.append({
                    "type": "image",
                    "image_path": image["image_path"],
                    "page": image["page"],
                })
        except Exception as exc:
            caption_results.append({
                "page": image["page"],
                "image_path": image["image_path"],
                "caption": None,
                "error": str(exc),
            })
            print(f"Warning: failed to caption {image['image_path']}: {exc}")

    all_chunks = text_chunks + image_texts
    all_metadatas = text_metadatas + image_metadatas

    build_index(all_chunks, FAISS_INDEX_PATH, metadatas=all_metadatas)

    return {
        "filename": file.filename,
        "text_chunks_created": len(text_chunks),
        "images_found": len(images),
        "images_captioned": sum(1 for c in caption_results if c.get("caption")),
        "captions": caption_results,
    }


@router.post("/ingest-images")
async def ingest_images(files: list[UploadFile] = File(...)):
    Path(IMAGE_UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

    captions = []
    for file in files:
        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        supported = {"png", "jpg", "jpeg", "gif", "bmp", "webp"}
        if ext not in supported:
            captions.append({
                "filename": file.filename,
                "caption": None,
                "error": "Unsupported image format",
            })
            continue

        img_path = os.path.join(IMAGE_UPLOAD_DIR, file.filename)
        with open(img_path, "wb") as out_file:
            shutil.copyfileobj(file.file, out_file)

        try:
            caption = caption_image(img_path)
            captions.append({
                "filename": file.filename,
                "image_path": img_path,
                "caption": caption,
            })
        except Exception as exc:
            captions.append({
                "filename": file.filename,
                "image_path": img_path,
                "caption": None,
                "error": str(exc),
            })

    return {
        "total_uploaded": len(files),
        "images_captioned": sum(1 for c in captions if c.get("caption")),
        "captions": captions,
    }


@router.get("/test-retrieve")
def test_retrieve(q: str, k: int = 3):
    try:
        store = load_index(FAISS_INDEX_PATH)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to load index: {exc}")

    results = query_index(store, q, k=k)
    return {"query": q, "results": results}


@router.get("/image/{path:path}")
def serve_image(path: str):
    full_path = os.path.join(os.getcwd(), path)
    if os.path.isfile(full_path):
        return FileResponse(full_path)
    raise HTTPException(status_code=404, detail="Image not found")


@router.get("/", response_class=HTMLResponse)
def serve_ui():
    return HTMLResponse(UI_HTML)


UI_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Tutor Agent - Document Ingest</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0f172a;color:#e2e8f0;min-height:100vh;padding:2rem}
.container{max-width:900px;margin:0 auto}
h1{font-size:1.8rem;margin-bottom:.3rem;background:linear-gradient(135deg,#60a5fa,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.subtitle{color:#94a3b8;margin-bottom:2rem;font-size:.95rem}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;margin-bottom:2rem}
@media(max-width:640px){.grid{grid-template-columns:1fr}}
.card{background:#1e293b;border-radius:12px;padding:1.5rem;border:1px solid #334155}
.card h2{font-size:1.1rem;margin-bottom:1rem;color:#60a5fa}
.drop-zone{border:2px dashed #475569;border-radius:10px;padding:2rem;text-align:center;cursor:pointer;transition:all .2s;position:relative}
.drop-zone:hover,.drop-zone.dragover{border-color:#60a5fa;background:#1e3a5f}
.drop-zone input{position:absolute;inset:0;opacity:0;cursor:pointer}
.drop-zone .icon{font-size:2rem;margin-bottom:.5rem}
.drop-zone .hint{color:#94a3b8;font-size:.85rem}
.file-list{display:flex;flex-wrap:wrap;gap:.4rem;margin-top:1rem}
.file-tag{background:#334155;border-radius:6px;padding:.25rem .6rem;font-size:.8rem;color:#cbd5e1}
.btn{background:linear-gradient(135deg,#3b82f6,#8b5cf6);color:white;border:none;border-radius:8px;padding:.7rem 1.5rem;font-size:1rem;cursor:pointer;transition:opacity .2s;width:100%;margin-top:1rem;font-weight:600}
.btn:hover{opacity:.85}
.btn:disabled{opacity:.4;cursor:not-allowed}
.status{text-align:center;padding:.8rem;border-radius:8px;margin-bottom:1rem;display:none}
.status.active{display:block}
.status.loading{background:#1e3a5f;color:#93c5fd;border:1px solid #3b82f6}
.status.success{background:#064e3b;color:#6ee7b7;border:1px solid #10b981}
.status.error{background:#450a0a;color:#fca5a5;border:1px solid #ef4444}
.results{margin-top:2rem;display:none}
.results.active{display:block}
.results h2{font-size:1.1rem;margin-bottom:1rem;color:#34d399}
.summary-cards{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin-bottom:1.5rem}
.summary-card{background:#1e293b;border-radius:10px;padding:1rem;text-align:center;border:1px solid #334155}
.summary-card .num{font-size:1.8rem;font-weight:700;color:#60a5fa}
.summary-card .label{font-size:.8rem;color:#94a3b8;margin-top:.2rem}
.caption-list{list-style:none}
.caption-item{background:#1e293b;border-radius:8px;padding:1rem;margin-bottom:.75rem;border:1px solid #334155}
.caption-item .file{font-weight:600;color:#a78bfa;font-size:.9rem}
.caption-item .page{font-size:.8rem;color:#64748b;margin-left:.5rem}
.caption-item .text{color:#cbd5e1;margin-top:.4rem;font-size:.9rem;line-height:1.5}
.caption-item .error{color:#f87171;font-size:.85rem;margin-top:.3rem}
.caption-item .img-preview{max-width:200px;margin-top:.5rem;border-radius:6px;border:1px solid #334155}
.spinner{display:inline-block;width:1rem;height:1rem;border:2px solid #93c5fd;border-top-color:transparent;border-radius:50%;animation:spin .6s linear;vertical-align:middle;margin-right:.4rem}
@keyframes spin{to{transform:rotate(360deg)}}
</style>
</head>
<body>
<div class="container">
<h1>Tutor Agent</h1>
<p class="subtitle">Upload course material — PDFs or standalone images — to build the knowledge base</p>

<div class="grid">
<div class="card">
<h2> Upload PDF</h2>
<div class="drop-zone" id="pdfDrop">
<input type="file" id="pdfInput" accept=".pdf" multiple>
<div class="icon">📄</div>
<div class="hint">Drop PDF files here or click to browse</div>
<div class="file-list" id="pdfFiles"></div>
</div>
<button class="btn" id="pdfBtn" disabled>Ingest PDFs</button>
</div>

<div class="card">
<h2> Upload Images</h2>
<div class="drop-zone" id="imgDrop">
<input type="file" id="imgInput" accept="image/*" multiple>
<div class="icon">🖼️</div>
<div class="hint">Drop images here or click to browse</div>
<div class="file-list" id="imgFiles"></div>
</div>
<button class="btn" id="imgBtn" disabled>Caption Images</button>
</div>
</div>

<div class="status" id="status"></div>

<button class="btn" id="testBtn" style="margin-bottom:2rem;background:linear-gradient(135deg,#475569,#64748b)"> Test FAISS Retrieval</button>

<div class="results" id="results">
<h2> Results</h2>
<div class="summary-cards" id="summaryCards"></div>
<ul class="caption-list" id="captionList"></ul>
</div>
</div>

<script>
const pdfInput=document.getElementById('pdfInput');
const imgInput=document.getElementById('imgInput');
const pdfBtn=document.getElementById('pdfBtn');
const imgBtn=document.getElementById('imgBtn');
const status=document.getElementById('status');
const results=document.getElementById('results');
const summaryCards=document.getElementById('summaryCards');
const captionList=document.getElementById('captionList');

let pdfFiles=[];
let imgFiles=[];

pdfInput.addEventListener('change',()=>{pdfFiles=[...pdfInput.files];renderFileTags('pdfFiles',pdfFiles);pdfBtn.disabled=pdfFiles.length===0});
imgInput.addEventListener('change',()=>{imgFiles=[...imgInput.files];renderFileTags('imgFiles',imgFiles);imgBtn.disabled=imgFiles.length===0});

['pdfDrop','imgDrop'].forEach(id=>{
const el=document.getElementById(id);
el.addEventListener('dragover',e=>{e.preventDefault();el.classList.add('dragover')});
el.addEventListener('dragleave',()=>el.classList.remove('dragover'));
el.addEventListener('drop',e=>{e.preventDefault();el.classList.remove('dragover');
const files=[...e.dataTransfer.files];
if(id==='pdfDrop'){pdfFiles=files.filter(f=>f.name.toLowerCase().endsWith('.pdf'));pdfInput.files=e.dataTransfer.files;renderFileTags('pdfFiles',pdfFiles);pdfBtn.disabled=pdfFiles.length===0}
else{imgFiles=files.filter(f=>f.type.startsWith('image/'));imgInput.files=e.dataTransfer.files;renderFileTags('imgFiles',imgFiles);imgBtn.disabled=imgFiles.length===0}
})});

function renderFileTags(listId,files){const el=document.getElementById(listId);el.innerHTML=files.map(f=>`<span class="file-tag">${f.name}</span>`).join('')}

function setStatus(msg,type){status.textContent=msg;status.className='status active '+type}

function showResults(summary,items){
results.classList.add('active');
summaryCards.innerHTML=Object.entries(summary).map(([k,v])=>`<div class="summary-card"><div class="num">${v}</div><div class="label">${k.replace(/_/g,' ')}</div></div>`).join('');
captionList.innerHTML=items.map(item=>{
const imgHtml=item.image_path?`<div><img class="img-preview" src="/image/${encodeURIComponent(item.image_path)}" alt="caption"></div>`:'';
const errHtml=item.error?`<div class="error"> Error: ${item.error}</div>`:'';
return `<li class="caption-item"><div><span class="file">${item.filename||item.image_path?.split('/').pop()||'Page '+item.page}</span>${item.page?`<span class="page">Page ${item.page}</span>`:''}</div>${item.caption?`<div class="text">${item.caption}</div>`:''}${imgHtml}${errHtml}</li>`
}).join('')
}

pdfBtn.addEventListener('click',async()=>{
setStatus('⏳ Processing PDFs...','loading');pdfBtn.disabled=true;
let total={text_chunks_created:0,images_found:0,images_captioned:0};
let allCaptions=[];
for(const file of pdfFiles){
const form=new FormData();form.append('file',file);
try{
const res=await fetch('/ingest',{method:'POST',body:form});
const data=await res.json();
total.text_chunks_created+=data.text_chunks_created;
total.images_found+=data.images_found;
total.images_captioned+=data.images_captioned;
allCaptions=allCaptions.concat(data.captions||[]);
}catch(e){setStatus(' Error: '+e.message,'error')}
}
setStatus(` Done! ${pdfFiles.length} PDF(s) ingested.`,'success');
showResults(total,allCaptions);pdfBtn.disabled=false
});

imgBtn.addEventListener('click',async()=>{
setStatus('⏳ Captioning images...','loading');imgBtn.disabled=true;
const form=new FormData();
imgFiles.forEach(f=>form.append('files',f));
try{
const res=await fetch('/ingest-images',{method:'POST',body:form});
const data=await res.json();
setStatus(` Done! ${data.images_captioned}/${data.total_uploaded} images captioned.`,'success');
showResults({total_uploaded:data.total_uploaded,images_captioned:data.images_captioned},data.captions);
}catch(e){setStatus(' Error: '+e.message,'error')}
imgBtn.disabled=false
});

document.getElementById('testBtn').addEventListener('click',async()=>{
const q=prompt('Enter a test query:');
if(!q)return;
setStatus('⏳ Querying FAISS...','loading');
try{
const res=await fetch(`/test-retrieve?q=${encodeURIComponent(q)}&k=3`);
const data=await res.json();
showResults({results:data.results.length,query:q},data.results.map(r=>({filename:'chunk',caption:r.text,image_path:r.metadata?.image_path,page:r.metadata?.page})));
setStatus(` Retrieved ${data.results.length} results.`,'success');
}catch(e){setStatus(' Error: '+e.message,'error')}
});
</script>
</body>
</html>"""
