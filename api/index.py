from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
import xmlrpc.client
import csv
import io
import os

app = FastAPI(title="Custom CRM API connected to Odoo 18")

# ==========================================
# CẤU HÌNH ODOO (Lấy từ biến môi trường để bảo mật trên GitHub)
# ==========================================
ODOO_URL = os.getenv("ODOO_URL")           # VD: "https://your-domain.odoo.com"
ODOO_DB = os.getenv("ODOO_DB")             # VD: "your_database_name"
ODOO_USERNAME = os.getenv("ODOO_USERNAME") # VD: "your_email@example.com"
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD") # VD: "your_api_key"

def get_odoo_connection():
    if not all([ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD]):
        raise HTTPException(status_code=500, detail="Thiếu cấu hình biến môi trường (Environment Variables)")
        
    try:
        common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
        uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
        if not uid:
            raise Exception("Sai thông tin đăng nhập Odoo")
        models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
        return uid, models
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi kết nối Odoo: {str(e)}")

# --- CÁC ENDPOINT ---

@app.get("/")
def read_root():
    return {"message": "API CRM đã lên sóng Vercel thành công!"}

@app.get("/api/leads")
def get_leads(limit: int = 50):
    uid, models = get_odoo_connection()
    fields = ['name', 'phone', 'partner_name', 'user_id', 'stage_id', 'type', 'tag_ids']
    
    leads = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'crm.lead', 'search_read',
        [[]], {'fields': fields, 'limit': limit}
    )
    return {"status": "success", "data": leads}

@app.get("/api/export")
def export_leads_csv():
    uid, models = get_odoo_connection()
    fields = ['name', 'phone', 'partner_name', 'type']
    
    leads = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'crm.lead', 'search_read',
        [[]], {'fields': fields}
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Ten', 'SDT', 'Cong Ty', 'Loai'])
    
    for lead in leads:
        writer.writerow([
            lead.get('name', ''),
            lead.get('phone', ''),
            lead.get('partner_name', ''),
            lead.get('type', 'lead')
        ])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads_export.csv"}
    )

@app.post("/api/import")
async def import_leads_csv(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Vui lòng upload file CSV")

    uid, models = get_odoo_connection()
    content = await file.read()
    reader = csv.reader(io.StringIO(content.decode('utf-8')))
    next(reader, None) # Bỏ header
    
    success_count = 0
    errors = []

    for row in reader:
        if len(row) < 3: continue
        try:
            lead_data = {
                'name': row[0],
                'phone': row[1],
                'partner_name': row[2],
                'type': 'lead'
            }
            models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'crm.lead', 'create', [lead_data])
            success_count += 1
        except Exception as e:
            errors.append(f"Lỗi dòng {row[0]}: {str(e)}")

    return {"message": "Import hoàn tất", "success_count": success_count, "errors": errors}