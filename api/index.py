from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from pydantic import BaseModel
from typing import List, Optional
import csv
import io
import json

app = FastAPI()

# --- DATABASE TẠM THỜI (Trong thực tế bạn nên kết nối Supabase/PostgreSQL) ---
# Dữ liệu mẫu ban đầu
db = {
    "leads": [
        {"id": 1, "name": "Nguyễn Văn A", "phone": "0901234567", "company": "Tech ABC", "consultant": "Admin", "referrer": "", "tags": "Hot", "status": "Có SĐT", "type": "lead"},
        {"id": 2, "name": "Trần Thị B", "phone": "0911222333", "company": "Global Corp", "consultant": "Sale 01", "referrer": "Nguyễn Văn A", "tags": "VIP", "status": "Đã PV", "type": "opportunity"}
    ],
    "counter": 3
}

# --- CẤU HÌNH STATUS ---
LEAD_STATUS = ["Có SĐT", "Có Zalo", "Đã tư vấn"]
OPPO_STATUS = ["Có CCCD", "Có lịch PV", "Đã PV", "Đã Đi Làm"]

# --- GIAO DIỆN (HTML & TAILWIND CSS) ---
def get_html_template(content):
    return f"""
    <html>
        <head>
            <title>Custom CRM Standalone</title>
            <script src="https://cdn.tailwindcss.com"></script>
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        </head>
        <body class="bg-gray-100 font-sans">
            <nav class="bg-[#714B67] text-white p-3 shadow-md flex justify-between items-center">
                <div class="flex space-x-6 items-center">
                    <span class="font-bold text-xl ml-4">CRM Beta</span>
                    <a href="/" class="hover:bg-[#5d3d55] px-3 py-1 rounded">Dashboard</a>
                    <a href="/export" class="hover:bg-[#5d3d55] px-3 py-1 rounded">Export</a>
                </div>
                <div class="mr-4"><i class="fas fa-user-circle text-2xl"></i></div>
            </nav>
            <div class="p-6">{content}</div>
        </body>
    </html>
    """

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    leads = [item for item in db["leads"] if item["type"] == "lead"]
    oppos = [item for item in db["leads"] if item["type"] == "opportunity"]
    
    html_content = f"""
    <div class="flex justify-between items-center mb-6">
        <h2 class="text-2xl font-semibold text-gray-700">Quản lý Khách hàng</h2>
        <button onclick="document.getElementById('addModal').showModal()" class="bg-[#00A09D] text-white px-4 py-2 rounded shadow hover:bg-[#008a87]">+ Tạo mới Lead</button>
    </div>

    <div class="grid grid-cols-2 gap-8">
        <div class="bg-gray-200 p-4 rounded-lg">
            <h3 class="font-bold text-[#714B67] mb-4 uppercase flex justify-between">
                <span><i class="fas fa-filter"></i> Leads (Tiềm năng)</span>
                <span class="bg-gray-400 text-white px-2 rounded-full text-sm">{len(leads)}</span>
            </h3>
            <div class="space-y-3">
                {"".join([card_template(item) for item in leads])}
            </div>
        </div>

        <div class="bg-blue-50 p-4 rounded-lg border-l-4 border-blue-400">
            <h3 class="font-bold text-blue-700 mb-4 uppercase flex justify-between">
                <span><i class="fas fa-trophy"></i> Opportunities (Cơ hội)</span>
                <span class="bg-blue-400 text-white px-2 rounded-full text-sm">{len(oppos)}</span>
            </h3>
            <div class="space-y-3">
                {"".join([card_template(item) for item in oppos])}
            </div>
        </div>
    </div>

    <dialog id="addModal" class="p-6 rounded-lg shadow-2xl w-96">
        <form action="/add" method="post" class="space-y-4">
            <h3 class="text-xl font-bold border-b pb-2">Thêm Lead mới</h3>
            <input name="name" placeholder="Tên khách hàng" class="w-full border p-2 rounded" required>
            <input name="phone" placeholder="Số điện thoại" class="w-full border p-2 rounded" required>
            <input name="company" placeholder="Công ty" class="w-full border p-2 rounded">
            <input name="consultant" placeholder="Người tư vấn" class="w-full border p-2 rounded">
            <select name="referrer" class="w-full border p-2 rounded">
                <option value="">-- Chọn Người giới thiệu --</option>
                {"".join([f'<option value="{l["name"]}">{l["name"]}</option>' for l in db["leads"]])}
            </select>
            <input name="tags" placeholder="Tags (cách nhau bởi dấu phẩy)" class="w-full border p-2 rounded">
            <div class="flex justify-end space-x-2">
                <button type="button" onclick="this.closest('dialog').close()" class="bg-gray-300 px-4 py-2 rounded">Hủy</button>
                <button type="submit" class="bg-[#00A09D] text-white px-4 py-2 rounded">Lưu Lead</button>
            </div>
        </form>
    </dialog>
    """
    return get_html_template(html_content)

def card_template(item):
    btn_convert = ""
    if item["type"] == "lead":
        btn_convert = f'<a href="/convert/{item["id"]}" class="text-xs text-blue-600 font-bold hover:underline">Chuyển thành Oppo</a>'
    
    status_color = "bg-green-100 text-green-800" if item["type"] == "lead" else "bg-purple-100 text-purple-800"
    
    return f"""
    <div class="bg-white p-4 rounded shadow-sm border-l-4 border-[#714B67] hover:shadow-md transition">
        <div class="flex justify-between items-start">
            <h4 class="font-bold text-gray-800">{item['name']}</h4>
            <span class="text-[10px] px-2 py-0.5 rounded-full {status_color}">{item['status']}</span>
        </div>
        <p class="text-sm text-gray-600"><i class="fas fa-phone fa-xs"></i> {item['phone']}</p>
        <p class="text-sm text-gray-500 italic"><i class="fas fa-building fa-xs"></i> {item['company']}</p>
        <div class="mt-2 pt-2 border-t flex justify-between items-center">
            <span class="text-[11px] text-gray-400">TV: {item['consultant']}</span>
            {btn_convert}
        </div>
    </div>
    """

# --- BACKEND LOGIC ---

@app.post("/add")
async def add_lead(name: str = Form(...), phone: str = Form(...), company: str = Form(""), 
                   consultant: str = Form(""), referrer: str = Form(""), tags: str = Form("")):
    new_id = db["counter"]
    db["leads"].append({
        "id": new_id, "name": name, "phone": phone, "company": company, 
        "consultant": consultant, "referrer": referrer, "tags": tags, 
        "status": "Có SĐT", "type": "lead"
    })
    db["counter"] += 1
    return RedirectResponse(url="/", status_code=303)

@app.get("/convert/{{item_id}}")
async def convert_to_opportunity(item_id: int):
    for item in db["leads"]:
        if item["id"] == item_id:
            item["type"] = "opportunity"
            item["status"] = "Có CCCD"
            break
    return RedirectResponse(url="/", status_code=303)

@app.get("/export")
def export_data():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Tên", "SĐT", "Công ty", "Trạng thái", "Loại"])
    for item in db["leads"]:
        writer.writerow([item["id"], item["name"], item["phone"], item["company"], item["status"], item["type"]])
    return Response(content=output.getvalue(), media_type="text/csv", headers={{"Content-Disposition": "attachment; filename=crm_data.csv"}})