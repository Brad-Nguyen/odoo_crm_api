from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response
import csv, io, os, motor.motor_asyncio
from bson import ObjectId

app = FastAPI()

# Kết nối MongoDB từ biến môi trường
MONGO_URL = os.getenv("MONGODB_URI")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client.crm_database
collection = db.leads

def layout(content):
    return f"""
    <html><head><title>BRAD CRM PRO</title><script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet"></head>
    <body class="bg-gray-100 min-h-screen">
    <nav class="bg-black text-white p-4 flex justify-between shadow-xl">
        <div class="flex items-center gap-6"><span class="text-xl font-bold">BRAD CRM PRO</span><a href="/" class="hover:text-gray-300">Dashboard</a></div>
        <div class="flex gap-4">
            <form action="/import" method="post" enctype="multipart/form-data" class="flex items-center bg-white/10 p-1 rounded border border-white/20">
                <input type="file" name="file" class="text-[10px] w-32" required><button type="submit" class="bg-blue-600 px-2 py-1 rounded text-[10px]">IMPORT</button>
            </form>
            <a href="/export" class="bg-green-600 px-4 py-1 rounded text-xs font-bold hover:bg-green-700">EXPORT CSV</a>
        </div>
    </nav>
    <div class="p-8 max-w-6xl mx-auto">{content}</div>
    </body></html>"""

@app.get("/", response_class=HTMLResponse)
async def home():
    items = await collection.find().to_list(length=1000)
    leads = "".join([card(i) for i in items if i.get('type') == 'lead'])
    oppos = "".join([card(i) for i in items if i.get('type') == 'opportunity'])
    
    content = f"""
    <div class="flex justify-between items-center mb-8">
        <h1 class="text-3xl font-black">PIPELINE <span class="text-blue-600">DATABASE LIVE</span></h1>
        <button onclick="addModal.showModal()" class="bg-black text-white px-6 py-3 rounded-xl shadow-lg hover:scale-105 transition">+ TẠO KHÁCH MỚI</button>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div class="bg-gray-200 p-6 rounded-3xl"><h2 class="font-bold mb-6 text-gray-500">LEADS</h2><div class="space-y-4">{leads}</div></div>
        <div class="bg-blue-100 p-6 rounded-3xl border-l-8 border-blue-500"><h2 class="font-bold mb-6 text-blue-700">OPPORTUNITIES</h2><div class="space-y-4">{oppos}</div></div>
    </div>
    <dialog id="addModal" class="p-8 rounded-3xl shadow-2xl w-96 backdrop:bg-black/50">
        <form action="/add" method="post" class="flex flex-col gap-4">
            <h3 class="text-xl font-bold">THÊM KHÁCH MỚI</h3>
            <input name="name" placeholder="Tên" class="border p-3 rounded-xl" required>
            <input name="phone" placeholder="SĐT" class="border p-3 rounded-xl">
            <input name="company" placeholder="Công ty" class="border p-3 rounded-xl">
            <button type="submit" class="bg-blue-600 text-white p-3 rounded-xl font-bold mt-2">LƯU VÀO DATABASE</button>
            <button type="button" onclick="addModal.close()" class="text-gray-400">Hủy</button>
        </form>
    </dialog>"""
    return layout(content)

def card(i):
    _id = str(i['_id'])
    return f"""
    <div class="bg-white p-5 rounded-2xl shadow-sm relative group hover:shadow-xl transition-all">
        <div class="flex justify-between items-center mb-2">
            <strong class="text-lg">{i['name']}</strong>
            <a href="/delete/{_id}" class="text-red-300 hover:text-red-600 transition p-2"><i class="fas fa-trash"></i></a>
        </div>
        <div class="text-sm text-gray-500">{i.get('phone', 'N/A')} | {i.get('company', 'N/A')}</div>
        <div class="mt-4 flex justify-between items-center border-t pt-3">
            <span class="text-[10px] bg-gray-100 px-3 py-1 rounded-full font-bold uppercase tracking-wider">{i.get('status', 'Mới')}</span>
            <div class="flex gap-2">
                <a href="/edit-view/{_id}" class="text-[11px] bg-gray-800 text-white px-3 py-2 rounded-lg font-bold">SỬA</a>
                {f'<a href="/convert/{_id}" class="text-[11px] bg-blue-600 text-white px-3 py-2 rounded-lg font-bold">LÊN OPPO</a>' if i['type']=='lead' else ''}
            </div>
        </div>
    </div>"""

@app.get("/edit-view/{{id}}", response_class=HTMLResponse)
async def edit_view(id: str):
    item = await collection.find_one({{"_id": ObjectId(id)}})
    if not item: return RedirectResponse("/")
    content = f"""
    <div class="max-w-md mx-auto bg-white p-10 rounded-3xl shadow-2xl mt-12 border border-gray-100 text-center">
        <h2 class="text-2xl font-black mb-8">CHỈNH SỬA</h2>
        <form action="/update/{id}" method="post" class="flex flex-col gap-5 text-left">
            <input name="name" value="{item['name']}" class="border-b-2 p-2 outline-none focus:border-blue-600 text-lg font-bold">
            <input name="phone" value="{item.get('phone','')}" class="border-b-2 p-2 outline-none focus:border-blue-600">
            <input name="company" value="{item.get('company','')}" class="border-b-2 p-2 outline-none focus:border-blue-600">
            <select name="status" class="border-b-2 p-2 outline-none">
                { "".join([f'<option value="{s}" {"selected" if item.get("status")==s else ""}>{s}</option>' for s in ["Có SĐT", "Có Zalo", "Đã tư vấn", "Có CCCD", "Đã PV", "Đã Đi Làm"]]) }
            </select>
            <button type="submit" class="bg-black text-white p-4 rounded-2xl font-bold mt-4 shadow-lg">CẬP NHẬT</button>
            <a href="/" class="text-gray-400 font-bold text-sm mt-4">QUAY LẠI</a>
        </form></div>"""
    return layout(content)

@app.post("/add")
async def add(name: str=Form(...), phone: str=Form(""), company: str=Form("")):
    await collection.insert_one({{"name": name, "phone": phone, "company": company, "status": "Có SĐT", "type": "lead"}})
    return RedirectResponse("/", 303)

@app.post("/update/{{id}}")
async def update(id: str, name: str=Form(...), phone: str=Form(""), company: str=Form(""), status: str=Form("")):
    await collection.update_one({{"_id": ObjectId(id)}}, {{"$set": {{"name": name, "phone": phone, "company": company, "status": status}}}})
    return RedirectResponse("/", 303)

@app.get("/delete/{{id}}")
async def delete(id: str):
    await collection.delete_one({{"_id": ObjectId(id)}})
    return RedirectResponse("/", 303)

@app.get("/convert/{{id}}")
async def convert(id: str):
    await collection.update_one({{"_id": ObjectId(id)}}, {{"$set": {{"type": "opportunity", "status": "Có CCCD"}}}})
    return RedirectResponse("/", 303)

@app.get("/export")
async def export_csv():
    items = await collection.find().to_list(length=1000)
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(["Ten", "SDT", "Cong Ty", "Trang Thai", "Loai"])
    for i in items: cw.writerow([i['name'], i.get('phone',''), i.get('company',''), i.get('status',''), i.get('type','')])
    return Response(content=si.getvalue(), media_type="text/csv", headers={{"Content-Disposition": "attachment; filename=crm_db_export.csv"}})

@app.post("/import")
async def import_csv(file: UploadFile = File(...)):
    content = await file.read()
    reader = csv.reader(io.StringIO(content.decode('utf-8')))
    next(reader, None)
    for r in reader:
        if r and len(r) >= 3:
            await collection.insert_one({{"name": r[0], "phone": r[1], "company": r[2], "status": "Có SĐT", "type": "lead"}})
    return RedirectResponse("/", 303)