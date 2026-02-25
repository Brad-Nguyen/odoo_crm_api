from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response
import csv, io

app = FastAPI()

# Database lưu trong bộ nhớ (Reset khi deploy/restart)
db = {"items": [
    {"id": 1, "name": "Nguyễn Văn A", "phone": "0901234567", "company": "Tech ABC", "status": "Có SĐT", "type": "lead"}
], "counter": 2}

def layout(content):
    return f"""
    <html><head><title>CRM FINAL</title><script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet"></head>
    <body class="bg-gray-50">
    <nav class="bg-black text-white p-4 flex justify-between items-center shadow-xl">
        <div class="flex items-center gap-8"><span class="text-xl font-black tracking-tighter">BRAD CRM FINAL</span><a href="/" class="text-gray-300 hover:text-white">Dashboard</a></div>
        <div class="flex gap-4">
            <form action="/import" method="post" enctype="multipart/form-data" class="bg-white/10 p-1 rounded flex items-center border border-white/20">
                <input type="file" name="file" class="text-[10px] w-32" required><button type="submit" class="bg-blue-600 px-2 py-1 rounded text-[10px] font-bold">IMPORT</button>
            </form>
            <a href="/export" class="bg-green-600 px-4 py-2 rounded-md hover:bg-green-700 text-xs font-bold shadow-lg">EXPORT CSV</a>
        </div>
    </nav>
    <div class="p-8 max-w-7xl mx-auto">{content}</div>
    </body></html>"""

@app.get("/", response_class=HTMLResponse)
async def home():
    leads = "".join([card(i) for i in db["items"] if i["type"] == "lead"])
    oppos = "".join([card(i) for i in db["items"] if i["type"] == "opportunity"])
    content = f"""
    <div class="flex justify-between items-center mb-10">
        <h1 class="text-3xl font-black text-gray-900">PIPELINE QUẢN LÝ</h1>
        <button onclick="addModal.showModal()" class="bg-indigo-600 text-white px-8 py-3 rounded-full font-bold shadow-xl hover:scale-105 transition">+ TẠO KHÁCH MỚI</button>
    </div>
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-12">
        <div class="bg-gray-100 p-6 rounded-3xl border border-gray-200">
            <h2 class="font-black text-gray-400 mb-6 flex justify-between items-center"><span>LEADS</span><span class="text-xs">NHÓM TIỀM NĂNG</span></h2>
            <div class="space-y-4">{leads}</div>
        </div>
        <div class="bg-white p-6 rounded-3xl border-2 border-indigo-100 shadow-inner">
            <h2 class="font-black text-indigo-600 mb-6 flex justify-between items-center"><span>OPPORTUNITIES</span><span class="text-xs">NHÓM CƠ HỘI</span></h2>
            <div class="space-y-4">{oppos}</div>
        </div>
    </div>
    <dialog id="addModal" class="p-8 rounded-3xl shadow-2xl w-full max-w-md backdrop:bg-black/50">
        <form action="/add" method="post" class="flex flex-col gap-5">
            <h3 class="text-2xl font-black">THÊM KHÁCH MỚI</h3>
            <input name="name" placeholder="Họ và tên" class="border-2 p-3 rounded-xl focus:border-indigo-500 outline-none" required>
            <input name="phone" placeholder="Số điện thoại" class="border-2 p-3 rounded-xl">
            <input name="company" placeholder="Tên công ty" class="border-2 p-3 rounded-xl">
            <div class="flex justify-end gap-3 mt-4">
                <button type="button" onclick="addModal.close()" class="p-3 text-gray-400 font-bold">HỦY</button>
                <button type="submit" class="bg-indigo-600 text-white px-8 py-3 rounded-xl font-bold shadow-lg">LƯU THÔNG TIN</button>
            </div>
        </form>
    </dialog>"""
    return layout(content)

def card(i):
    return f"""
    <div class="bg-white p-6 rounded-2xl shadow-sm hover:shadow-xl transition-all border-l-8 {'border-gray-300' if i['type']=='lead' else 'border-indigo-600'} relative group">
        <div class="flex justify-between items-center mb-2">
            <strong class="text-xl text-gray-800">{i['name']}</strong>
            <a href="/delete/{i['id']}" class="text-red-300 hover:text-red-600 transition p-2"><i class="fas fa-trash"></i></a>
        </div>
        <div class="text-gray-500 font-medium mb-4"><i class="fas fa-phone-alt mr-2 text-xs"></i>{i['phone'] or 'N/A'} | <i class="fas fa-building mr-2 text-xs"></i>{i['company'] or 'N/A'}</div>
        <div class="flex justify-between items-center">
            <span class="text-[10px] font-black bg-gray-100 px-3 py-1 rounded-full uppercase tracking-widest">{i['status']}</span>
            <div class="flex gap-2">
                <a href="/edit-view/{i['id']}" class="text-[11px] bg-gray-800 text-white px-4 py-2 rounded-lg font-bold">SỬA</a>
                {f'<a href="/convert/{i["id"]}" class="text-[11px] bg-indigo-600 text-white px-4 py-2 rounded-lg font-bold">LÊN OPPO</a>' if i['type']=='lead' else ''}
            </div>
        </div>
    </div>"""

@app.get("/edit-view/{{id}}", response_class=HTMLResponse)
async def edit_view(id: int):
    item = next((i for i in db["items"] if i["id"] == id), None)
    if not item: return RedirectResponse("/")
    content = f"""
    <div class="max-w-md mx-auto bg-white p-10 rounded-3xl shadow-2xl mt-12 border border-gray-100">
        <h2 class="text-3xl font-black mb-8 text-indigo-600">CHỈNH SỬA</h2>
        <form action="/update/{id}" method="post" class="flex flex-col gap-5">
            <div class="flex flex-col"><label class="text-[10px] font-black text-gray-400 mb-1">HỌ TÊN</label>
            <input name="name" value="{item['name']}" class="border-b-2 p-2 outline-none focus:border-indigo-600 text-lg font-bold"></div>
            <div class="flex flex-col"><label class="text-[10px] font-black text-gray-400 mb-1">SỐ ĐIỆN THOẠI</label>
            <input name="phone" value="{item['phone']}" class="border-b-2 p-2 outline-none focus:border-indigo-600"></div>
            <div class="flex flex-col"><label class="text-[10px] font-black text-gray-400 mb-1">CÔNG TY</label>
            <input name="company" value="{item['company']}" class="border-b-2 p-2 outline-none focus:border-indigo-600"></div>
            <div class="flex flex-col"><label class="text-[10px] font-black text-gray-400 mb-1">TRẠNG THÁI</label>
            <select name="status" class="border-b-2 p-2 outline-none bg-transparent">
                { "".join([f'<option value="{s}" {"selected" if item["status"]==s else ""}>{s}</option>' for s in ["Có SĐT", "Có Zalo", "Đã tư vấn", "Có CCCD", "Đã PV", "Đã Đi Làm"]]) }
            </select></div>
            <button type="submit" class="bg-indigo-600 text-white p-4 rounded-2xl font-bold shadow-lg mt-4 hover:bg-indigo-700 transition">CẬP NHẬT NGAY</button>
            <a href="/" class="text-center text-gray-400 font-bold text-sm mt-4">QUAY LẠI</a>
        </form></div>"""
    return layout(content)

@app.post("/add")
async def do_add(name: str=Form(...), phone: str=Form(""), company: str=Form("")):
    db["items"].append({"id": db["counter"], "name": name, "phone": phone, "company": company, "status": "Có SĐT", "type": "lead"})
    db["counter"] += 1
    return RedirectResponse("/", 303)

@app.post("/update/{{id}}")
async def do_up(id: int, name: str=Form(...), phone: str=Form(""), company: str=Form(""), status: str=Form("")):
    for i in db["items"]:
        if i["id"] == id: i.update({"name": name, "phone": phone, "company": company, "status": status})
    return RedirectResponse("/", 303)

@app.get("/delete/{{id}}")
async def do_del(id: int):
    db["items"] = [i for i in db["items"] if i["id"] != id]
    return RedirectResponse("/", 303)

@app.get("/convert/{{id}}")
async def do_conv(id: int):
    for i in db["items"]:
        if i["id"] == id: i["type"], i["status"] = "opportunity", "Có CCCD"
    return RedirectResponse("/", 303)

@app.get("/export")
def do_exp():
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(["Ten", "SDT", "Cong Ty", "Trang Thai"])
    for i in db["items"]: cw.writerow([i["name"], i["phone"], i["company"], i["status"]])
    return Response(content=si.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=crm_export.csv"})

@app.post("/import")
async def do_imp(file: UploadFile = File(...)):
    content = await file.read()
    reader = csv.reader(io.StringIO(content.decode('utf-8')))
    next(reader, None)
    for r in reader:
        if r and len(r) >= 3:
            db["items"].append({"id": db["counter"], "name": r[0], "phone": r[1], "company": r[2], "status": "Có SĐT", "type": "lead"})
            db["counter"] += 1
    return RedirectResponse("/", 303)