from flask import Flask, render_template, request, redirect, url_for, send_file, flash
import pandas as pd
import os
from io import BytesIO
import openpyxl
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import logging
from dotenv import load_dotenv
from supabase import create_client, Client

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Inisialisasi Flask
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'supersecretkey')

# Filter kustom strftime
def format_datetime(value, format='%Y-%m-%d'):
    if value == 'now':
        return datetime.now().strftime(format)
    return value.strftime(format)

app.jinja_env.filters['strftime'] = format_datetime

# Validasi Supabase credentials
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("SUPABASE_URL or SUPABASE_KEY environment variable is not set")
    raise ValueError("SUPABASE_URL or SUPABASE_KEY environment variable is not set. Please configure it in .env.")

# Inisialisasi Supabase client
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info(f"Connected to Supabase at {SUPABASE_URL}")
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {str(e)}")
    raise RuntimeError(f"Failed to initialize Supabase client: {str(e)}")

LOCKED_UNITS = [
    "DZ3007", "DZ3014", "DZ3026","EX1022", "EX2017", "EX2027", "EX2032", "EX2033", "EX2040", "EX3009"
]
PENJATAHAN_MAP = {
    "DZ3007": 52, "DZ3014": 52, "DZ3026": 52,
    "EX1022": 58,
    "EX2017": 93, "EX2027": 93, "EX2032": 93 , "EX2033": 93, "EX2040": 93, 
    "EX3009": 126
}
MAX_CAPACITY_MAP = {
    "DZ3007": 1000, "DZ3014": 1000, "DZ3026": 1200,
    "EX1022": 980,
    "EX2017": 1380, "EX2027": 1380, "EX2032": 1380 , "EX2033": 1380, "EX2040": 1380, 
    "EX3009": 3400
}
INITIAL_HM_AWAL = {
    "DZ3007": 45280, "DZ3014": 45914, "DZ3026": 20090,
    "EX1022": 34288,
    "EX2017": 45720, "EX2027": 35080, "EX2032": 26684 , "EX2033": 25817, "EX2040": 18579, 
    "EX3009": 35514
}

# Fungsi data menggunakan Supabase API
def load_or_create_data():
    try:
        response = supabase.table('fuel_records').select('*').execute()
        records = response.data
        if records:
            df = pd.DataFrame([
                {
                    "Date": r["Date"].strip() if r["Date"] else "",
                    "NO_UNIT": r["NO_UNIT"].strip() if r["NO_UNIT"] else "",
                    "HM_AWAL": round(float(r["HM_AWAL"]), 2) if r["HM_AWAL"] else 0.0,
                    "HM_AKHIR": round(float(r["HM_AKHIR"]), 2) if r["HM_AKHIR"] else 0.0,
                    "SELISIH": round(float(r["SELISIH"]), 2) if r["SELISIH"] else 0.0,
                    "LITERAN": round(float(r["LITERAN"]), 2) if r["LITERAN"] else 0.0,
                    "PENJATAHAN": int(r["PENJATAHAN"]) if r["PENJATAHAN"] else 0,
                    "Max_Capacity": round(float(r["Max_Capacity"]), 2) if r["Max_Capacity"] else 0.0,
                    "Buffer_Stock": round(float(r["Buffer_Stock"]), 2) if r["Buffer_Stock"] else 0.0,
                    "is_new": bool(r["is_new"])
                } for r in records
            ])
            return df
        columns = [
            "Date", "NO_UNIT", "HM_AWAL", "HM_AKHIR", "SELISIH",
            "LITERAN", "PENJATAHAN", "Max_Capacity", "Buffer_Stock", "is_new"
        ]
        return pd.DataFrame(columns=columns)
    except Exception as e:
        logger.error(f"Error loading data from Supabase: {str(e)}")
        raise

def save_data(df):
    try:
        # Hapus semua data lama
        supabase.table('fuel_records').delete().gte('id', 0).execute()
        # Masukkan data baru
        for _, row in df.iterrows():
            record = {
                "Date": str(row["Date"]).strip(),
                "NO_UNIT": str(row["NO_UNIT"]).strip(),
                "HM_AWAL": float(row["HM_AWAL"]),
                "HM_AKHIR": float(row["HM_AKHIR"]),
                "SELISIH": float(row["SELISIH"]),
                "LITERAN": float(row["LITERAN"]),
                "PENJATAHAN": int(row["PENJATAHAN"]),
                "Max_Capacity": float(row["Max_Capacity"]),
                "Buffer_Stock": float(row["Buffer_Stock"]),
                "is_new": bool(row["is_new"])
            }
            supabase.table('fuel_records').insert(record).execute()
    except Exception as e:
        logger.error(f"Error saving data to Supabase: {str(e)}")
        raise

def reset_data():
    try:
        supabase.table('fuel_records').delete().gte('id', 0).execute()
    except Exception as e:
        logger.error(f"Error resetting data in Supabase: {str(e)}")
        raise

def backup_data():
    df = load_or_create_data()
    if not df.empty:
        df.to_csv("backup_fuel_data.csv", index=False)

def get_hm_awal(df, no_unit):
    unit_data = df[df["NO_UNIT"] == no_unit]
    if not unit_data.empty:
        return unit_data["HM_AKHIR"].iloc[-1]
    return INITIAL_HM_AWAL.get(no_unit, 0.0)

def get_penjatahan(no_unit):
    return PENJATAHAN_MAP.get(no_unit, 62)

def get_max_capacity(no_unit):
    return MAX_CAPACITY_MAP.get(no_unit, 0)

def add_new_record(no_unit, hm_akhir, date):
    df = load_or_create_data()
    hm_awal = get_hm_awal(df, no_unit)
    penjatahan = get_penjatahan(no_unit)
    max_capacity = get_max_capacity(no_unit)

    if hm_akhir <= hm_awal:
        return df, None, f"HM Akhir ({hm_akhir}) harus lebih besar dari HM Awal ({hm_awal})!"

    selisih = hm_akhir - hm_awal
    selisih = round(selisih, 2)
    literan = selisih * penjatahan
    buffer_stock = max_capacity - (selisih * penjatahan)

    new_record = {
        "Date": date.strftime("%Y-%m-%d"),
        "NO_UNIT": no_unit.strip(),
        "HM_AWAL": round(hm_awal, 2),
        "HM_AKHIR": round(hm_akhir, 2),
        "SELISIH": selisih,
        "LITERAN": round(literan, 2),
        "PENJATAHAN": penjatahan,
        "Max_Capacity": round(max_capacity, 2),
        "Buffer_Stock": round(buffer_stock, 2),
        "is_new": True
    }

    df.loc[df["NO_UNIT"] == no_unit, "is_new"] = False
    df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
    save_data(df)
    return df, new_record, None

def create_pdf_report(df, shift, date):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []

    styles = getSampleStyleSheet()
    title = Paragraph(
        f"PLAN REFUELING UNIT TRACK {date.strftime('%b %Y').upper()}"
        f"<br/>Shift: {shift} Tgl: {date.strftime('%d %b %Y')}",
        styles['Title']
    )
    elements.append(title)
    elements.append(Paragraph("<br/>", styles['Normal']))

    data = [["Date", "Unit", "Est HM Jam 12:00", "HM", "Qty Plan Refueling", "Note"]]
    for _, row in df.iterrows():
        qty_plan = f"{row['LITERAN']:.2f}" if row['LITERAN'] > 0 else "Full" if row['Buffer_Stock'] <= 0 else "-"
        data.append([
            row["Date"],
            row["NO_UNIT"],
            f"{row['HM_AWAL']:.2f}",
            f"{row['SELISIH']:.2f}",
            qty_plan,
            ""
        ])

    col_widths = [80, 60, 100, 60, 100, 100]
    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.goldenrod),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    return buffer

# Routes
@app.route('/favicon.ico')
def favicon():
    try:
        return send_file(os.path.join(app.root_path, 'static', 'favicon.ico'))
    except FileNotFoundError:
        logger.warning("Favicon not found, returning 204")
        return '', 204

@app.route('/')
def index():
    try:
        df = load_or_create_data()
        units = LOCKED_UNITS
        selected_unit = request.args.get('unit', units[0])
        current_unit_data = df[df["NO_UNIT"] == selected_unit]
        last_hm_akhir = get_hm_awal(df, selected_unit)

        filter_unit = request.args.get('filter_unit', 'Semua')
        if filter_unit == 'Semua':
            filtered_df = df
        else:
            filtered_df = df[df["NO_UNIT"] == filter_unit]

        unique_units = ['Semua'] + sorted(df["NO_UNIT"].unique().tolist()) if not df.empty else ['Semua']
        return render_template(
            'index.html',
            units=units,
            selected_unit=selected_unit,
            last_hm_akhir=last_hm_akhir,
            filtered_df=filtered_df.to_dict(orient='records'),
            filter_unit=filter_unit,
            unique_units=unique_units
        )
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        flash("Gagal memuat data. Silakan coba lagi nanti.", 'error')
        return render_template('index.html', units=LOCKED_UNITS, selected_unit='', last_hm_akhir=0.0, filtered_df=[], filter_unit='Semua', unique_units=['Semua'])

@app.route('/add_record', methods=['POST'])
def add_record():
    try:
        no_unit = request.form['no_unit'].strip()
        hm_akhir = float(request.form['hm_akhir'])
        date = datetime.strptime(request.form['date'], '%Y-%m-%d')

        df, record, error = add_new_record(no_unit, hm_akhir, date)
        if error:
            flash(error, 'error')
        else:
            flash(
                f"Data untuk unit {no_unit} berhasil disimpan! "
                f"Buffer Stock: <span style='color:#facc15;font-weight:bold'>{record['Buffer_Stock']:.2f}</span> | "
                f"Literan: <span style='color:#facc15;font-weight:bold'>{record['LITERAN']:.2f}</span>",
                'success'
            )
        return redirect(url_for('index', unit=no_unit))
    except Exception as e:
        logger.error(f"Error in add_record: {str(e)}")
        flash("Gagal menambahkan data. Silakan coba lagi.", 'error')
        return redirect(url_for('index'))

@app.route('/export_all')
def export_all():
    try:
        df = load_or_create_data()
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        output.seek(0)
        return send_file(output, download_name='fuel_data_all.xlsx', as_attachment=True)
    except Exception as e:
        logger.error(f"Error in export_all: {str(e)}")
        flash("Gagal mengekspor data. Silakan coba lagi.", 'error')
        return redirect(url_for('index'))

@app.route('/export_unit/<unit>')
def export_unit(unit):
    try:
        df = load_or_create_data()
        df_unit = df[df["NO_UNIT"] == unit]
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_unit.to_excel(writer, index=False)
        output.seek(0)
        return send_file(output, download_name=f'fuel_data_{unit}.xlsx', as_attachment=True)
    except Exception as e:
        logger.error(f"Error in export_unit: {str(e)}")
        flash("Gagal mengekspor data unit. Silakan coba lagi.", 'error')
        return redirect(url_for('index'))

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    try:
        report_date = datetime.strptime(request.form['report_date'], '%Y-%m-%d')
        shift = request.form['shift']
        df = load_or_create_data()
        report_df = df[df["Date"] == report_date.strftime("%Y-%m-%d")]
        if not report_df.empty:
            pdf_buffer = create_pdf_report(report_df, shift, report_date)
            return send_file(
                pdf_buffer,
                download_name=f"Plan_Refueling_Hauler_{report_date.strftime('%d_%b_%Y')}_Shift_{shift}.pdf",
                as_attachment=True
            )
        else:
            flash(f"Tidak ada data untuk tanggal {report_date.strftime('%d %b %Y')}.", 'error')
            return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error in generate_pdf: {str(e)}")
        flash("Gagal menghasilkan PDF. Silakan coba lagi.", 'error')
        return redirect(url_for('index'))

@app.route('/reset_data', methods=['POST'])
def reset_data_route():
    try:
        backup_data()
        reset_data()
        flash("Semua data berhasil dihapus! Backup telah dibuat.", 'success')
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error in reset_data: {str(e)}")
        flash("Gagal mereset data. Silakan coba lagi.", 'error')
        return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)