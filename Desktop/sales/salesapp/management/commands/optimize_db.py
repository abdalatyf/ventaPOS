import os
import shutil
import sqlite3
import sys

# 1. تحديد المسارات
# اسم قاعدة البيانات الحالية في مشروعك (تأكد من الاسم)
CURRENT_DB_NAME = 'db.sqlite3'  # أو 'db.sqlite3' حسب ما عندك
APP_NAME = 'SalesApp_Secure' # اسم الفولدر في AppData
NEW_DB_NAME = 'system_core.bin' # الاسم الجديد المموه

# تحديد مسار AppData/Local
local_app_data = os.environ.get('LOCALAPPDATA')
if not local_app_data:
    print("❌ خطأ: لم يتم العثور على مسار AppData.")
    sys.exit(1)

# المسار الجديد الكامل
DEST_DIR = os.path.join(local_app_data, APP_NAME)
DEST_PATH = os.path.join(DEST_DIR, NEW_DB_NAME)

def migrate_and_optimize():
    print("--- 🚀 بدء عملية النقل والتحسين ---")

    # 2. إنشاء المجلد الآمن
    if not os.path.exists(DEST_DIR):
        os.makedirs(DEST_DIR)
        print(f"✅ تم إنشاء المجلد الآمن: {DEST_DIR}")

    # 3. نقل الملف (نسخ)
    if os.path.exists(CURRENT_DB_NAME):
        try:
            shutil.copy2(CURRENT_DB_NAME, DEST_PATH)
            print(f"✅ تم نقل قاعدة البيانات وتغيير اسمها إلى: {NEW_DB_NAME}")
        except Exception as e:
            print(f"❌ خطأ أثناء النقل: {e}")
            sys.exit(1)
    else:
        # لو مفيش داتا بيز قديمة، هننشئ واحدة جديدة هناك
        print("⚠️ لم يتم العثور على قاعدة بيانات قديمة، سيتم إنشاء واحدة جديدة.")

    # 4. تفعيل وضع السرعة (WAL Mode)
    try:
        conn = sqlite3.connect(DEST_PATH)
        cursor = conn.cursor()
        
        # تفعيل WAL (للسرعة القصوى وعدم التوقف)
        cursor.execute("PRAGMA journal_mode=WAL;")
        wal_result = cursor.fetchone()[0]
        
        # تفعيل التزامن الطبيعي (أسرع وآمن بما يكفي)
        cursor.execute("PRAGMA synchronous=NORMAL;")
        
        # زيادة حجم الكاش
        cursor.execute("PRAGMA cache_size=-64000;") # 64MB cache
        
        conn.close()
        
        print(f"✅ تم تفعيل وضع السرعة (Journal Mode: {wal_result})")
        print("---------------------------------------")
        print("🎉 العملية تمت بنجاح!")
        print(f"المسار الجديد للقاعدة هو:\n{DEST_PATH}")
        print("---------------------------------------")
        
    except Exception as e:
        print(f"❌ خطأ أثناء تحسين الأداء: {e}")

if __name__ == "__main__":
    migrate_and_optimize()