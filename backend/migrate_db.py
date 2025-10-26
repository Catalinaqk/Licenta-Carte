#!/usr/bin/env python3
"""
Script de migrație pentru baza de date
Adaugă coloanele noi: descriere, rezumat_ai
"""

import psycopg2
from psycopg2.extras import RealDictCursor

# Conexiune la baza de date
conn = psycopg2.connect(
    host="localhost",
    database="licenta_db",
    user="postgres",
    password="Opel2807*",
    port=5432
)

cur = conn.cursor()

try:
    print("🔄 Încep migrația bazei de date...")
    
    # Verifică dacă coloana descriere există
    print("📝 Verific coloana 'descriere'...")
    cur.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name='carti' AND column_name='descriere'
    """)
    if not cur.fetchone():
        print("  → Adaug coloana 'descriere'...")
        cur.execute("""
            ALTER TABLE carti
            ADD COLUMN descriere TEXT DEFAULT NULL
        """)
        print("  ✅ Coloana 'descriere' adăugată")
    else:
        print("  ✅ Coloana 'descriere' există deja")
    
    # Verifică dacă coloana rezumat_ai există
    print("📝 Verific coloana 'rezumat_ai'...")
    cur.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name='carti' AND column_name='rezumat_ai'
    """)
    if not cur.fetchone():
        print("  → Adaug coloana 'rezumat_ai'...")
        cur.execute("""
            ALTER TABLE carti
            ADD COLUMN rezumat_ai TEXT DEFAULT NULL
        """)
        print("  ✅ Coloana 'rezumat_ai' adăugată")
    else:
        print("  ✅ Coloana 'rezumat_ai' există deja")
    
    conn.commit()
    print("\n✅ Migrație completă! Baza de date e actualizată.")
    print("\n🔄 Acum trebuie să repornești backend-ul:")
    print("   python app.py")
    
except Exception as e:
    print(f"❌ Eroare la migrație: {e}")
    conn.rollback()
finally:
    cur.close()
    conn.close()
