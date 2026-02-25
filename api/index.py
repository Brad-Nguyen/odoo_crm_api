from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response
import csv, io, os, motor.motor_asyncio
from bson import ObjectId

app = FastAPI()

# 1. Kết nối MongoDB từ biến môi trường MONGODB_URI trên Vercel
MONGO_URL = os.getenv("MONGODB_URI")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client.crm_live
collection = db.leads

# 2. Giao diện chung (Layout)
def layout(content):
    return f"""
    <html><head><title>BRAD CRM PRO</title><script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet"></head>
    <body class="bg-slate-50 min-h-screen">
    <nav class="bg-slate-900 text-white p-4 flex justify-between items-center shadow-xl">
        <div class="flex items-center gap-6">
            <span class="text-xl font-bold tracking-tight text-white">BRAD CRM <span class="text-blue-500">PRO</span></span>
            <a href="/" class="text-slate-400 hover:text-white transition font-medium">Dashboard</a>
        </div>
        <div class="flex gap-4">
            <form action="/import" method="post" enctype="multipart/form-data" class="bg-white/5 p-1 rounded border border-white/10 flex items-center">
                <input type="file" name="file" class="text-[10px] w-32" required>
                <button type="submit" class="bg-blue-600 px-2 py-1 rounded text-[10px] font-bold hover:bg-blue-700">IMPORT</button>
            </form>
            <a href="/export" class="bg-emerald-600 px-4 py-1 rounded text-xs font-bold hover:bg-emerald-700 shadow-md flex items-center">
                <i class="fas fa-download mr-1"></i> EXPORT CSV
            </a>
        </div>
    </nav>
    <div class="p-8 max-w-7xl mx-auto">{content}</div>
    </body></html>"""

# 3. Trang chủ - Dashboard
@app.get("/", response_class=HTMLResponse)
async def home():
    items = await collection.find().to_list(length=1000)
    leads = "".join([card(i) for i in items if i.get('type') == 'lead'])
    oppos = "".join([card(i) for i in items if i.get('type') == 'opportunity'])
    
    content = f"""
    <div class="flex justify-between items-center mb-10">
        <div>
            <h1 class="text-3xl font-black text-slate-800 uppercase tracking-tighter">Hệ thống Live Data</h1>
            <p class="text-sm text-slate-400">Database: MongoDB Atlas (Live Connection)</p>
        </div>
        <button onclick="addModal.showModal()" class="bg-blue-600 text-white px-8 py-3 rounded-2xl shadow-lg hover:bg-blue-700 transition-all font-bold">+ TẠO KHÁCH MỚI</button>
    </div>
    
    <div class="grid grid-cols-1 md:grid-cols-2 gap-10">
        <div class="bg-slate-200/50 p-6 rounded-3xl border border-slate-200 shadow-inner">
            <h2 class="font-black mb-6 text-slate-400 uppercase tracking-widest text-sm flex justify-between">
                <span>Leads (Tiềm năng)</span>
                <span class="bg-slate-300 text-white px-2 py-0.5 rounded-full text-[10px]">{len([i for i in items if i.get('type')=='lead'])}</span>
            </h2>
            <div class="space-y-4">{leads or '<p class="text-center text-slate-400 py-10 italic text-sm">Chưa có Lead nào</p>'}</div>
        </div>
        
        <div class="bg-blue-50 p-6 rounded-3xl border-l-8 border-blue-500 shadow-sm">
            <h2 class="font-black mb-6 text-blue-700 uppercase tracking-widest text-sm flex justify-between">
                <span>Opportunities (Cơ hội)</span>
                <span class="bg-blue-500 text-white px-2 py-0.5 rounded-full text-[10px]">{len([i for i in items if i.get('type')=='opportunity'])}</span>
            </h2>
            <div class="space-y-4">{oppos or '<p class="text-center text-blue-300 py-10 italic text-sm">Chưa có Cơ hội nào</p>'}</div>
        </div>
    </div>

    <dialog id="addModal" class="p-8 rounded-3xl shadow-2xl w-96 backdrop:bg-slate-900/50">
        <form action="/add" method="post" class="flex flex-col gap-4">
            <h3 class="text-xl font-bold text-center mb-2">THÊM KHÁCH MỚI</h3>
            <input name="name" placeholder="Họ và tên" class="border p-3 rounded-xl outline-none focus:border-blue-500 bg-slate-50" required>
            <input name="phone" placeholder="Số điện thoại" class="border p-3 rounded-xl outline-none focus:border-blue-500 bg-slate-50">
            <input name="company" placeholder="Công ty" class="border p-3 rounded-xl outline-none focus:border-blue-500 bg-slate-50">
            <button type="submit" class="bg-blue-600 text-white p-3 rounded-xl font-bold mt-2 shadow-md hover:bg-blue-700 transition">LƯU VÀO DATABASE</button>
            <button type="button" onclick="addModal.close()" class="text-slate-400 text-sm mt-2 text-center hover:text-slate-600 font-medium">Đóng</button>
        </form>
    </dialog>"""
    return layout(content)

# 4. Giao diện thẻ khách hàng
def card(i):
    _id = str(i['_id'])
    return f"""
    <div class="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 relative group hover:shadow-xl transition-all">
        <div class="flex justify-between items-center mb-2">
            <strong class="text-lg text-slate-800">{i['name']}</strong>
            <a href="/delete/{_id}" class="text-slate-200 hover:text-red-500 transition p-2" onclick="return confirm('Xóa khách này?')"><i class="fas fa-trash"></i></a>
        </div>
        <div class="text-sm text-slate-400 mb-4 font-medium"><i class="fas fa-phone fa-xs mr-1"></i> {i.get('phone', 'N/A')} | <i class="fas fa-building fa-xs mr-1"></i> {i.get('company', 'N/A')}</div>
        <div class="flex justify-between items-center border-t pt-3">
            <span class="text-[9px] bg-slate-100 text-slate-500 px-3 py-1 rounded-full font-black uppercase tracking-widest">{i.get('status', 'Mới')}</span>
            <div class="flex gap-2">
                <a href="/edit-view/{_id}" class="text-[10px] bg-slate-800 text-white px-4 py-2 rounded-lg font-bold hover:bg-slate-700 transition">SỬA</a>
                {f'<a href="/convert/{_id}" class="text-[10px] bg-blue-600 text-white px-4 py-2 rounded-lg font-bold hover:bg-blue-700 transition shadow-sm">LÊN OPPO</a>' if i.get('type')=='lead' else ''}
            </div>
        </div>
    </div>"""

# 5. Xử lý Logic Backend

@app.post("/add")
async def add(name: str=Form(...), phone: str=Form(""), company: str=Form("")):
    await collection.insert_one({{"name": name, "phone": phone, "company": company, "status": "Có SĐT", "type": "lead"}})
    return RedirectResponse(url="/", status_code=303)

@app.get("/delete/{{id}}")
async def delete(id: str):
    await collection.delete_one({{"_id": ObjectId(id)}})
    return RedirectResponse(url="/", status_code=303)

@app.get("/convert/{{id}}")
async def convert(id: str):
    # Fix 404: Đảm bảo route này hoạt động và cập nhật đúng bản ghi
    await collection.update_one({{"_id": ObjectId(id)}}, {{"$set": {{"type": "opportunity", "status": "Có CCCD"}}}})
    return RedirectResponse(url="/", status_code=303)

@app.get("/edit-view/{{id}}", response_class=HTMLResponse)
async def edit_view(id: str):
    item = await collection.find_one({{"_id": ObjectId(id)}})
    if not item: return RedirectResponse("/")
    content = f"""
    <div class="max-w-md mx-auto bg-white p-10 rounded-3xl shadow-2xl mt-12 border border-slate-100">
        <h2 class="text-2xl font-black mb-8 text-slate-800 text-center uppercase tracking-tight italic">Chỉnh sửa thông tin</h2>
        <form action="/update/{id}" method="post" class="flex flex-col gap-6 text-left">
            <div class="flex flex-col"><label class="text-[10px] font-bold text-slate-400 mb-1 uppercase ml-1">Họ tên</label>
            <input name="name" value="{item['name']}" class="border-b-2 p-2 outline-none focus:border-blue-600 text-lg font-bold bg-transparent"></div>
            
            <div class="flex flex-col"><label class="text-[10px] font-bold text-slate-400 mb-1 uppercase ml-1">Số điện thoại</label>
            <input name="phone" value="{item.get('phone','')}" class="border-b-2 p-2 outline-none focus:border-blue-600 bg-transparent"></div>
            
            <div class="flex flex-col"><label class="text-[10px] font-bold text-slate-400 mb-1 uppercase ml-1">Công ty</label>
            <input name="company" value="{item.get('company','')}" class="border-b-2 p-2 outline-none focus:border-blue-600 bg-transparent"></div>
            
            <div class="flex flex-col"><label class="text-[10px] font-bold text-slate-400 mb-1 uppercase ml-1">Trạng thái hiện tại</label>
            <select name="status" class="border-b-2 p-2 outline-none bg-transparent font-bold">
                { "".join([f'<option value="{s}" {"selected" if item.get("status")==s else ""}>{s}</option>' for s in ["Có SĐT", "Có Zalo", "Đã tư vấn", "Có CCCD", "Đã PV", "Đã Đi Làm"]]) }
            </select></div>
            
            <button type="submit" class="bg-blue-600 text-white p-4 rounded-2xl font-bold mt-4 shadow-lg hover:bg-blue-700 transition">CẬP NHẬT NGAY</button>
            <a href="/" class="text-center text-slate-400 font-bold text-sm mt-2 hover:text-slate-600">HUỶ & QUAY LẠI</a>
        </form></div>"""
    return layout(content)

@app.post("/update/{{id}}")
async def update(id: str, name: str=Form(...), phone: str=Form(""), company: str=Form(""), status: str=Form("")):
    await collection.update_one({{"_id": ObjectId(id)}}, {{"$set": {{"name": name, "phone": phone, "company": company, "status": status}}}})
    return RedirectResponse(url="/", status_code=303)

@app.get("/export")
async def export_csv():
    items = await collection.find().to_list(length=1000)
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(["Ten", "SDT", "Cong Ty", "Trang Thai", "Loai"])
    for i in items: cw.writerow([i['name'], i.get('phone',''), i.get('company',''), i.get('status',''), i.get('type','')])
    return Response(content=si.getvalue(), media_type="text/csv", headers={{"Content-Disposition": "attachment; filename=crm_data.csv"}})

@app.post("/import")
async def import_csv(file: UploadFile = File(...)):
    content = await file.read()
    reader = csv.reader(io.StringIO(content.decode('utf-8')))
    next(reader, None) # Bỏ qua header
    for r in reader:
        if r and len(r) >= 3:
            await collection.insert_one({{"name": r[0], "phone": r[1], "company": r[2], "status": "Có SĐT", "type": "lead"}})
    return RedirectResponse(url="/", status_code=303)