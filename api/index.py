from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response
import csv, io, os, motor.motor_asyncio, asyncio
from bson import ObjectId

app = FastAPI()

# Kết nối Database thật (MongoDB)
MONGO_URL = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client.crm_database
collection = db.leads

def layout(content):
    return f"""
    <html><head><title>BRAD CRM PRO</title><script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet"></head>
    <body class="bg-gray-100"><nav class="bg-black text-white p-4 flex justify-between shadow-xl">
    <div class="flex items-center gap-6"><span class="text-xl font-bold">BRAD CRM PRO</span><a href="/">Dashboard</a></div>
    <div class="flex gap-4">
        <form action="/import" method="post" enctype="multipart/form-data" class="flex items-center bg-white/10 p-1 rounded">
            <input type="file" name="file" class="text-[10px] w-32" required><button type="submit" class="bg-blue-600 px-2 py-1 rounded text-[10px]">IMPORT</button>
        </form>
        <a href="/export" class="bg-green-600 px-4 py-1 rounded text-xs font-bold hover:bg-green-700">EXPORT CSV</a>
    </div></nav><div class="p-8">{content}</div></body></html>"""

@app.get("/", response_class=HTMLResponse)
async def home():
    cursor = collection.find()
    items = await cursor.to_list(length=1000)
    leads = "".join([card(i) for i in items if i.get('type') == 'lead'])
    oppos = "".join([card(i) for i in items if i.get('type') == 'opportunity'])
    
    content = f"""
    <div class="flex justify-between mb-8">
        <h1 class="text-2xl font-bold">Dữ liệu vĩnh viễn (MongoDB)</h1>
        <button onclick="addModal.showModal()" class="bg-indigo-600 text-white px-6 py-2 rounded shadow-lg">+ Tạo Lead</button>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div class="bg-gray-200 p-6 rounded-2xl">
            <h2 class="font-bold text-gray-600 mb-4">LEADS</h2><div class="space-y-4">{leads}</div>
        </div>
        <div class="bg-indigo-50 p-6 rounded-2xl border-l-4 border-indigo-500">
            <h2 class="font-bold text-indigo-700 mb-4">OPPORTUNITIES</h2><div class="space-y-4">{oppos}</div>
        </div>
    </div>
    <dialog id="addModal" class="p-8 rounded-2xl shadow-2xl w-96">
        <form action="/add" method="post" class="flex flex-col gap-4">
            <h3 class="text-xl font-bold">Thêm Khách Mới</h3>
            <input name="name" placeholder="Tên" class="border p-2 rounded" required>
            <input name="phone" placeholder="SĐT" class="border p-2 rounded">
            <input name="company" placeholder="Công ty" class="border p-2 rounded">
            <button type="submit" class="bg-indigo-600 text-white p-2 rounded">Lưu vào Database</button>
            <button type="button" onclick="addModal.close()" class="text-gray-400 text-sm">Hủy</button>
        </form>
    </dialog>"""
    return layout(content)

def card(i):
    _id = str(i['_id'])
    return f"""
    <div class="bg-white p-5 rounded-xl shadow-sm relative group">
        <div class="flex justify-between">
            <strong class="text-lg">{i['name']}</strong>
            <a href="/delete/{_id}" class="text-red-400 hover:text-red-600"><i class="fas fa-trash"></i></a>
        </div>
        <p class="text-sm text-gray-500">{i.get('phone', 'N/A')} | {i.get('company', 'N/A')}</p>
        <div class="mt-4 flex justify-between items-center">
            <span class="text-[10px] bg-gray-100 px-2 py-1 rounded font-bold uppercase">{i.get('status', 'Mới')}</span>
            <div class="flex gap-2">
                <a href="/edit-view/{_id}" class="text-xs bg-gray-100 px-3 py-1 rounded">Sửa</a>
                {f'<a href="/convert/{_id}" class="text-xs bg-indigo-600 text-white px-3 py-1 rounded">Lên Oppo</a>' if i['type']=='lead' else ''}
            </div>
        </div>
    </div>"""

@app.post("/add")
async def add(name: str=Form(...), phone: str=Form(""), company: str=Form("")):
    await collection.insert_one({"name": name, "phone": phone, "company": company, "status": "Có SĐT", "type": "lead"})
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
    cursor = collection.find()
    items = await cursor.to_list(length=1000)
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(["Ten", "SDT", "Cong Ty", "Trang Thai"])
    for i in items: cw.writerow([i['name'], i.get('phone',''), i.get('company',''), i.get('status','')])
    return Response(content=si.getvalue(), media_type="text/csv", headers={{"Content-Disposition": "attachment; filename=data.csv"}})

@app.post("/import")
async def import_csv(file: UploadFile = File(...)):
    content = await file.read()
    reader = csv.reader(io.StringIO(content.decode('utf-8')))
    next(reader, None)
    for r in reader:
        if r and len(r) >= 3:
            await collection.insert_one({{"name": r[0], "phone": r[1], "company": r[2], "status": "Có SĐT", "type": "lead"}})
    return RedirectResponse("/", 303)