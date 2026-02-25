from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response
import csv, io

app = FastAPI()

# Database tạm thời
db = {"items": [
    {"id": 1, "name": "Khách mẫu", "phone": "0912345678", "company": "Công ty X", "status": "Có SĐT", "type": "lead"}
], "counter": 2}

def layout(content):
    # Thêm Version ID để kiểm tra cache: VERSION_1.1
    return f"""
    <html><head><title>CRM v1.1</title><script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet"></head>
    <body class="bg-slate-100">
    <nav class="bg-[#714B67] text-white p-4 flex justify-between shadow-lg">
        <div class="flex items-center gap-6"><span class="text-xl font-bold">BRAD CRM v1.1</span><a href="/">Dashboard</a></div>
        <div class="flex gap-4">
            <form action="/import" method="post" enctype="multipart/form-data" class="bg-white/10 p-1 rounded flex items-center">
                <input type="file" name="file" class="text-[10px] w-32" required><button type="submit" class="bg-blue-500 px-2 py-1 rounded text-[10px]">Import</button>
            </form>
            <a href="/export" class="bg-green-600 px-4 py-1 rounded hover:bg-green-700 text-sm">Export CSV</a>
        </div>
    </nav>
    <div class="p-8">{content}</div>
    </body></html>"""

@app.get("/", response_class=HTMLResponse)
async def home():
    leads = "".join([card(i) for i in db["items"] if i["type"] == "lead"])
    oppos = "".join([card(i) for i in db["items"] if i["type"] == "opportunity"])
    content = f"""
    <div class="flex justify-between mb-8">
        <h1 class="text-2xl font-bold text-slate-800">Pipeline Manager <span class="text-sm font-normal text-gray-400">(v1.1)</span></h1>
        <button onclick="addModal.showModal()" class="bg-[#00A09D] text-white px-6 py-2 rounded shadow">+ Tạo Lead Mới</button>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-10">
        <div class="bg-slate-200 p-6 rounded-xl">
            <h2 class="font-bold text-[#714B67] mb-4 uppercase italic">--- Cột Leads ---</h2><div class="space-y-4">{leads}</div>
        </div>
        <div class="bg-blue-100 p-6 rounded-xl border-l-8 border-blue-500">
            <h2 class="font-bold text-blue-700 mb-4 uppercase italic">--- Cột Opportunities ---</h2><div class="space-y-4">{oppos}</div>
        </div>
    </div>
    <dialog id="addModal" class="p-8 rounded-2xl shadow-2xl w-96">
        <form action="/add" method="post" class="flex flex-col gap-4">
            <h3 class="text-xl font-bold">Thêm Khách Mới</h3>
            <input name="name" placeholder="Tên khách" class="border p-2 rounded" required>
            <input name="phone" placeholder="Số điện thoại" class="border p-2 rounded">
            <input name="company" placeholder="Công ty" class="border p-2 rounded">
            <div class="flex justify-end gap-2 mt-4">
                <button type="button" onclick="addModal.close()" class="p-2 text-gray-400">Đóng</button>
                <button type="submit" class="bg-[#00A09D] text-white px-4 py-2 rounded">Lưu ngay</button>
            </div>
        </form>
    </dialog>"""
    return layout(content)

def card(i):
    return f"""
    <div class="bg-white p-5 rounded-lg shadow-sm border-r-4 {'border-gray-400' if i['type']=='lead' else 'border-blue-500'} relative group">
        <div class="flex justify-between">
            <strong class="text-lg">{i['name']}</strong>
            <a href="/delete/{i['id']}" class="text-red-400 hover:text-red-600 opacity-0 group-hover:opacity-100 transition"><i class="fas fa-trash"></i></a>
        </div>
        <div class="text-sm text-slate-500 mt-1">{i['phone'] or 'N/A'} | {i['company'] or 'N/A'}</div>
        <div class="mt-4 flex justify-between items-center">
            <span class="text-[10px] bg-slate-100 px-2 py-1 rounded-full font-bold uppercase">{i['status']}</span>
            <div class="flex gap-2">
                <a href="/edit-page/{i['id']}" class="text-[11px] bg-slate-200 px-3 py-1 rounded hover:bg-slate-300">SỬA</a>
                {f'<a href="/convert/{i["id"]}" class="text-[11px] bg-blue-600 text-white px-3 py-1 rounded">LÊN OPPO</a>' if i['type']=='lead' else ''}
            </div>
        </div>
    </div>"""

@app.get("/edit-page/{{id}}", response_class=HTMLResponse)
async def edit_page(id: int):
    item = next((i for i in db["items"] if i["id"] == id), None)
    if not item: return RedirectResponse("/")
    content = f"""
    <div class="max-w-md mx-auto bg-white p-8 rounded-2xl shadow-xl mt-10">
        <h2 class="text-2xl font-bold mb-6 text-[#714B67]">Sửa khách hàng</h2>
        <form action="/update/{id}" method="post" class="flex flex-col gap-4">
            <label class="text-xs font-bold text-gray-400 uppercase">Họ tên</label>
            <input name="name" value="{item['name']}" class="border-b p-2 focus:border-[#714B67] outline-none">
            <label class="text-xs font-bold text-gray-400 uppercase">SĐT</label>
            <input name="phone" value="{item['phone']}" class="border-b p-2 focus:border-[#714B67] outline-none">
            <label class="text-xs font-bold text-gray-400 uppercase">Công ty</label>
            <input name="company" value="{item['company']}" class="border-b p-2 focus:border-[#714B67] outline-none">
            <label class="text-xs font-bold text-gray-400 uppercase">Trạng thái</label>
            <select name="status" class="border-b p-2 outline-none">
                { "".join([f'<option value="{s}" {"selected" if item["status"]==s else ""}>{s}</option>' for s in ["Có SĐT", "Có Zalo", "Đã tư vấn", "Có CCCD", "Đã PV", "Đã Đi Làm"]]) }
            </select>
            <button type="submit" class="bg-[#714B67] text-white p-3 rounded-full mt-6 shadow-lg">LƯU THAY ĐỔI</button>
            <a href="/" class="text-center text-gray-400 text-sm mt-2">Hủy bỏ</a>
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
        if i["id"] == id:
            i.update({"name": name, "phone": phone, "company": company, "status": status})
    return RedirectResponse("/", 303)

@app.get("/delete/{{id}}")
async def do_del(id: int):
    db["items"] = [i for i in db["items"] if i["id"] != id]
    return RedirectResponse("/", 303)

@app.get("/convert/{{id}}")
async def do_conv(id: int):
    for i in db["items"]:
        if i["id"] == id:
            i["type"], i["status"] = "opportunity", "Có CCCD"
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