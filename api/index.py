from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response
import csv, io, os, motor.motor_asyncio
from bson import ObjectId

app = FastAPI()

# Kết nối MongoDB
MONGO_URL = os.getenv("MONGODB_URI")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client.crm_live
collection = db.leads

def layout(content):
    return f"""
    <html><head><title>BRAD CRM PRO</title><script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet"></head>
    <body class="bg-slate-50 min-h-screen">
    <nav class="bg-slate-900 text-white p-4 flex justify-between items-center shadow-xl">
        <div class="flex items-center gap-6"><span class="text-xl font-bold tracking-tight text-white">BRAD CRM PRO</span><a href="/" class="text-slate-400 hover:text-white transition">Dashboard</a></div>
        <div class="flex gap-4">
            <form action="/api/import" method="post" enctype="multipart/form-data" class="bg-white/5 p-1 rounded border border-white/10 flex items-center">
                <input type="file" name="file" class="text-[10px] w-32" required><button type="submit" class="bg-blue-600 px-2 py-1 rounded text-[10px] font-bold">IMPORT</button>
            </form>
            <a href="/api/export" class="bg-emerald-600 px-4 py-1 rounded text-xs font-bold shadow-md">EXPORT CSV</a>
        </div>
    </nav>
    <div class="p-8 max-w-7xl mx-auto text-slate-800">{content}</div>
    </body></html>"""

@app.get("/", response_class=HTMLResponse)
@app.get("/api", response_class=HTMLResponse)
async def home():
    items = await collection.find().to_list(length=1000)
    leads = "".join([card(i) for i in items if i.get('type') == 'lead'])
    oppos = "".join([card(i) for i in items if i.get('type') == 'opportunity'])
    
    content = f"""
    <div class="flex justify-between items-center mb-10">
        <h1 class="text-3xl font-black uppercase tracking-tighter">Hệ thống Live Data</h1>
        <button onclick="addModal.showModal()" class="bg-blue-600 text-white px-8 py-3 rounded-2xl shadow-lg font-bold hover:bg-blue-700 transition">+ TẠO KHÁCH MỚI</button>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-10">
        <div class="bg-slate-200/50 p-6 rounded-3xl border border-slate-200 shadow-inner">
            <h2 class="font-black mb-6 text-slate-400 uppercase tracking-widest text-sm">Leads</h2>
            <div class="space-y-4">{leads or '<p class="text-center text-slate-400 py-10">Trống</p>'}</div>
        </div>
        <div class="bg-blue-50 p-6 rounded-3xl border-l-8 border-blue-500 shadow-sm">
            <h2 class="font-black mb-6 text-blue-700 uppercase tracking-widest text-sm">Opportunities</h2>
            <div class="space-y-4">{oppos or '<p class="text-center text-blue-300 py-10 text-sm">Trống</p>'}</div>
        </div>
    </div>
    <dialog id="addModal" class="p-8 rounded-3xl shadow-2xl w-96 backdrop:bg-slate-900/50">
        <form action="/api/add" method="post" class="flex flex-col gap-4">
            <h3 class="text-xl font-bold text-center">THÊM MỚI</h3>
            <input name="name" placeholder="Họ tên" class="border p-3 rounded-xl outline-none focus:border-blue-500" required>
            <input name="phone" placeholder="SĐT" class="border p-3 rounded-xl">
            <input name="company" placeholder="Công ty" class="border p-3 rounded-xl">
            <button type="submit" class="bg-blue-600 text-white p-3 rounded-xl font-bold shadow-md">LƯU DATABASE</button>
            <button type="button" onclick="addModal.close()" class="text-slate-400 text-sm">Hủy</button>
        </form>
    </dialog>"""
    return layout(content)

def card(i):
    _id = str(i['_id'])
    return f"""
    <div class="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 relative group">
        <div class="flex justify-between items-center mb-2">
            <strong class="text-lg text-slate-800">{i['name']}</strong>
            <a href="/api/delete/{_id}" class="text-slate-200 hover:text-red-500 p-2" onclick="return confirm('Xóa?')"><i class="fas fa-trash"></i></a>
        </div>
        <div class="text-sm text-slate-400 mb-4">{i.get('phone', 'N/A')} | {i.get('company', 'N/A')}</div>
        <div class="flex justify-between items-center border-t pt-3">
            <span class="text-[9px] bg-slate-100 px-3 py-1 rounded-full font-black uppercase">{i.get('status', 'Mới')}</span>
            <div class="flex gap-2">
                <a href="/api/edit-view/{_id}" class="text-[10px] bg-slate-800 text-white px-4 py-2 rounded-lg font-bold">SỬA</a>
                {f'<a href="/api/convert/{_id}" class="text-[10px] bg-blue-600 text-white px-4 py-2 rounded-lg font-bold shadow-sm">LÊN OPPO</a>' if i.get('type')=='lead' else ''}
            </div>
        </div>
    </div>"""

# --- CÁC HÀM XỬ LÝ (QUAN TRỌNG: CÓ TIỀN TỐ /api/...) ---

@app.post("/api/add")
async def add(name: str=Form(...), phone: str=Form(""), company: str=Form("")):
    await collection.insert_one({"name": name, "phone": phone, "company": company, "status": "Có SĐT", "type": "lead"})
    return RedirectResponse(url="/", status_code=303)

@app.get("/api/delete/{id}")
async def delete(id: str):
    await collection.delete_one({"_id": ObjectId(id)})
    return RedirectResponse(url="/", status_code=303)

@app.get("/api/convert/{id}")
async def convert(id: str):
    await collection.update_one({"_id": ObjectId(id)}, {"$set": {"type": "opportunity", "status": "Có CCCD"}})
    return RedirectResponse(url="/", status_code=303)

@app.get("/api/edit-view/{id}", response_class=HTMLResponse)
async def edit_view(id: str):
    item = await collection.find_one({"_id": ObjectId(id)})
    if not item: return RedirectResponse("/")
    content = f"""
    <div class="max-w-md mx-auto bg-white p-10 rounded-3xl shadow-2xl mt-12">
        <h2 class="text-2xl font-black mb-8 text-center italic uppercase">Chỉnh sửa</h2>
        <form action="/api/update/{id}" method="post" class="flex flex-col gap-6 text-left">
            <input name="name" value="{item['name']}" class="border-b-2 p-2 outline-none focus:border-blue-600 text-lg font-bold">
            <input name="phone" value="{item.get('phone','')}" class="border-b-2 p-2 outline-none focus:border-blue-600">
            <input name="company" value="{item.get('company','')}" class="border-b-2 p-2 outline-none focus:border-blue-600">
            <select name="status" class="border-b-2 p-2 outline-none bg-transparent font-bold text-blue-600 uppercase text-xs">
                { "".join([f'<option value="{s}" {"selected" if item.get("status")==s else ""}>{s}</option>' for s in ["Có SĐT", "Có Zalo", "Đã tư vấn", "Có CCCD", "Đã PV", "Đã Đi Làm"]]) }
            </select>
            <button type="submit" class="bg-black text-white p-4 rounded-2xl font-bold mt-4 shadow-lg">CẬP NHẬT</button>
            <a href="/" class="text-center text-gray-400 font-bold text-sm mt-4">HUỶ & QUAY LẠI</a>
        </form></div>"""
    return layout(content)

@app.post("/api/update/{id}")
async def update(id: str, name: str=Form(...), phone: str=Form(""), company: str=Form(""), status: str=Form("")):
    await collection.update_one({"_id": ObjectId(id)}, {"$set": {"name": name, "phone": phone, "company": company, "status": status}})
    return RedirectResponse(url="/", status_code=303)

@app.get("/api/export")
async def export_csv():
    items = await collection.find().to_list(length=1000)
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(["Ten", "SDT", "Cong Ty", "Trang Thai", "Loai"])
    for i in items: cw.writerow([i['name'], i.get('phone',''), i.get('company',''), i.get('status',''), i.get('type','')])
    return Response(content=si.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=crm_data.csv"})

@app.post("/api/import")
async def import_csv(file: UploadFile = File(...)):
    content = await file.read()
    reader = csv.reader(io.StringIO(content.decode('utf-8')))
    next(reader, None)
    for r in reader:
        if r and len(r) >= 3:
            await collection.insert_one({"name": r[0], "phone": r[1], "company": r[2], "status": "Có SĐT", "type": "lead"})
    return RedirectResponse(url="/", status_code=303)