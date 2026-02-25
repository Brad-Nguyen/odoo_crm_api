from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
import csv
import io
import json

app = FastAPI()

# --- DATABASE TẠM THỜI (Sẽ reset khi Vercel restart) ---
db = {
    "items": [
        {"id": 1, "name": "Nguyễn Văn A", "phone": "0901234567", "company": "Tech ABC", "consultant": "Admin", "referrer": "", "tags": "Hot", "status": "Có SĐT", "type": "lead"},
        {"id": 2, "name": "Trần Thị B", "phone": "0911222333", "company": "Global Corp", "consultant": "Sale 01", "referrer": "Nguyễn Văn A", "tags": "VIP", "status": "Đã PV", "type": "opportunity"}
    ],
    "counter": 3
}

# --- GIAO DIỆN UI (Tailwind CSS) ---
def get_html(content):
    return f"""
    <html>
        <head>
            <title>Custom CRM Standalone</title>
            <script src="https://cdn.tailwindcss.com"></script>
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        </head>
        <body class="bg-gray-100 min-h-screen">
            <nav class="bg-[#714B67] text-white p-3 flex justify-between items-center shadow-md">
                <div class="flex items-center space-x-6">
                    <span class="font-bold text-xl ml-4">CRM Manager</span>
                    <a href="/" class="hover:bg-[#5d3d55] px-3 py-1 rounded">Dashboard</a>
                </div>
                <div class="flex space-x-4 mr-4">
                    <form action="/import" method="post" enctype="multipart/form-data" class="flex items-center bg-white/10 p-1 rounded">
                        <input type="file" name="file" class="text-xs w-40" required>
                        <button type="submit" class="bg-blue-500 text-[10px] px-2 py-1 rounded">Import CSV</button>
                    </form>
                    <a href="/export" class="bg-green-600 px-4 py-1 rounded text-sm hover:bg-green-700"><i class="fas fa-download"></i> Export</a>
                </div>
            </nav>
            <div class="p-6">{content}</div>
        </body>
    </html>
    """

@app.get("/", response_class=HTMLResponse)
async def home():
    leads = [i for i in db["items"] if i["type"] == "lead"]
    oppos = [i for i in db["items"] if i["type"] == "opportunity"]
    
    content = f"""
    <div class="flex justify-between mb-6">
        <h2 class="text-2xl font-bold text-gray-700">Pipeline Quản lý</h2>
        <button onclick="document.getElementById('addModal').showModal()" class="bg-[#00A09D] text-white px-6 py-2 rounded shadow">+ Tạo Lead</button>
    </div>

    <div class="grid grid-cols-2 gap-8">
        <div class="bg-gray-200 p-4 rounded-lg">
            <h3 class="font-bold mb-4 text-[#714B67] uppercase">Leads ({len(leads)})</h3>
            <div class="space-y-3">{"".join([render_card(i) for i in leads])}</div>
        </div>
        <div class="bg-blue-50 p-4 rounded-lg border-l-4 border-blue-400">
            <h3 class="font-bold mb-4 text-blue-700 uppercase">Opportunities ({len(oppos)})</h3>
            <div class="space-y-3">{"".join([render_card(i) for i in oppos])}</div>
        </div>
    </div>

    <dialog id="addModal" class="p-6 rounded-lg shadow-xl w-[450px]">
        <form action="/add" method="post" class="space-y-4">
            <h3 class="text-xl font-bold border-b pb-2">Thêm Khách Hàng</h3>
            <div class="grid grid-cols-2 gap-2">
                <input name="name" placeholder="Tên" class="border p-2 rounded w-full" required>
                <input name="phone" placeholder="SĐT" class="border p-2 rounded w-full">
            </div>
            <input name="company" placeholder="Công ty" class="border p-2 rounded w-full">
            <input name="consultant" placeholder="Người tư vấn" class="border p-2 rounded w-full">
            <input name="tags" placeholder="Tags" class="border p-2 rounded w-full">
            <div class="flex justify-end space-x-2 pt-4">
                <button type="button" onclick="this.closest('dialog').close()" class="bg-gray-300 px-4 py-2 rounded">Hủy</button>
                <button type="submit" class="bg-[#00A09D] text-white px-4 py-2 rounded">Lưu</button>
            </div>
        </form>
    </dialog>
    """
    return get_html(content)

def render_card(i):
    return f"""
    <div class="bg-white p-4 rounded shadow hover:shadow-md transition group">
        <div class="flex justify-between items-start">
            <h4 class="font-bold text-gray-800">{i['name']}</h4>
            <div class="flex space-x-2 opacity-0 group-hover:opacity-100 transition">
                <a href="/delete/{i['id']}" class="text-red-500 hover:text-red-700"><i class="fas fa-trash"></i></a>
            </div>
        </div>
        <p class="text-sm text-gray-600">{i['phone'] or 'Chưa có SĐT'}</p>
        <p class="text-xs text-gray-400 italic">{i['company'] or 'N/A'}</p>
        <div class="mt-3 flex justify-between items-center border-t pt-2">
            <span class="text-[10px] bg-gray-100 px-2 py-1 rounded">{i['status']}</span>
            <div class="space-x-2">
                {f'<a href="/convert/{i["id"]}" class="text-xs text-blue-500 font-bold">Chuyển Oppo</a>' if i['type']=='lead' else ''}
                <button onclick="window.location.href='/edit-view/{i['id']}'" class="text-xs bg-gray-200 px-2 py-1 rounded">Sửa</button>
            </div>
        </div>
    </div>
    """

@app.get("/edit-view/{{id}}", response_class=HTMLResponse)
async def edit_view(id: int):
    item = next((i for i in db["items"] if i["id"] == id), None)
    if not item: return RedirectResponse("/")
    
    content = f"""
    <div class="max-w-md mx-auto bg-white p-8 rounded-xl shadow-lg">
        <h2 class="text-2xl font-bold mb-6 text-[#714B67]">Chỉnh sửa Thông tin</h2>
        <form action="/update/{id}" method="post" class="space-y-4">
            <div><label class="text-xs font-bold text-gray-500 uppercase">Tên</label>
            <input name="name" value="{item['name']}" class="w-full border-b p-2 focus:outline-none focus:border-[#714B67]"></div>
            <div><label class="text-xs font-bold text-gray-500 uppercase">SĐT</label>
            <input name="phone" value="{item['phone']}" class="w-full border-b p-2 focus:outline-none focus:border-[#714B67]"></div>
            <div><label class="text-xs font-bold text-gray-500 uppercase">Công ty</label>
            <input name="company" value="{item['company']}" class="w-full border-b p-2 focus:outline-none focus:border-[#714B67]"></div>
            <div><label class="text-xs font-bold text-gray-500 uppercase">Trạng thái</label>
            <input name="status" value="{item['status']}" class="w-full border-b p-2 focus:outline-none focus:border-[#714B67]"></div>
            <div class="flex justify-between pt-6">
                <a href="/" class="text-gray-500 py-2">Quay lại</a>
                <button type="submit" class="bg-[#714B67] text-white px-8 py-2 rounded-full">Cập nhật</button>
            </div>
        </form>
    </div>
    """
    return get_html(content)

# --- XỬ LÝ DỮ LIỆU ---

@app.post("/add")
async def add(name: str=Form(...), phone: str=Form(...), company: str=Form(""), consultant: str=Form(""), tags: str=Form("")):
    db["items"].append({{"id": db["counter"], "name": name, "phone": phone, "company": company, "consultant": consultant, "tags": tags, "status": "Có SĐT", "type": "lead"}})
    db["counter"] += 1
    return RedirectResponse("/", status_code=303)

@app.post("/update/{{id}}")
async def update(id: int, name: str=Form(...), phone: str=Form(...), company: str=Form(""), status: str=Form("")):
    for i in db["items"]:
        if i["id"] == id:
            i.update({{"name": name, "phone": phone, "company": company, "status": status}})
            break
    return RedirectResponse("/", status_code=303)

@app.get("/delete/{{id}}")
async def delete(id: int):
    db["items"] = [i for i in db["items"] if i["id"] != id]
    return RedirectResponse("/", status_code=303)

@app.get("/convert/{{id}}")
async def convert(id: int):
    for i in db["items"]:
        if i["id"] == id:
            i["type"], i["status"] = "opportunity", "Có CCCD"
            break
    return RedirectResponse("/", status_code=303)

@app.get("/export")
def export_csv():
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(["ID", "Name", "Phone", "Company", "Status", "Type"])
    for i in db["items"]:
        cw.writerow([i["id"], i["name"], i["phone"], i["company"], i["status"], i["type"]])
    return Response(content=si.getvalue(), media_type="text/csv", headers={{"Content-Disposition": "attachment; filename=crm_export.csv"}})

@app.post("/import")
async def import_csv(file: UploadFile = File(...)):
    content = await file.read()
    decoded = content.decode('utf-8').splitlines()
    reader = csv.reader(decoded)
    next(reader) # Bỏ header
    for row in reader:
        if len(row) >= 3:
            db["items"].append({{"id": db["counter"], "name": row[0], "phone": row[1], "company": row[2], "consultant": "Imported", "tags": "", "status": "Có SĐT", "type": "lead"}})
            db["counter"] += 1
    return RedirectResponse("/", status_code=303)