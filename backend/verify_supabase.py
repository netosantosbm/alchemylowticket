import os
import sys
from pathlib import Path
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.append(str(BACKEND_DIR))

load_dotenv(BACKEND_DIR / ".env")
load_dotenv(BACKEND_DIR.parent / ".env")

from sqlalchemy import inspect
from app.database import engine, Base
import models

def test_connection():
    print("=" * 60)
    print("🔍 VERIFICANDO CONEXÃO COM O SUPABASE POSTGRESQL")
    print("=" * 60)

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("⚠️  AVISO: 'DATABASE_URL' ainda não foi configurada no arquivo backend/.env.")
        print("💡 Por favor, configure sua Connection String do Supabase no backend/.env")
        return False

    # Mask password for display
    masked_url = db_url
    if "@" in db_url and ":" in db_url:
        parts = db_url.split("@")
        prefix = parts[0].split(":")
        if len(prefix) >= 3:
            masked_url = f"{prefix[0]}:{prefix[1]}:****@{parts[1]}"
    print(f"📡 Conectando a: {masked_url}")

    try:
        # Create all tables on Supabase
        print("\n🔨 Executando Base.metadata.create_all() no Supabase...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tabelas criadas com sucesso no Supabase!")

        # Inspect tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"\n📋 Tabelas encontradas no banco ({len(tables)}):")
        for t in tables:
            columns = [c["name"] for c in inspector.get_columns(t)]
            print(f"  • {t}: {', '.join(columns)}")

        print("\n✨ CONEXÃO E TABELAS NO SUPABASE VALIDADAS COM SUCESSO!")
        print("=" * 60)
        return True
    except Exception as e:
        print(f"\n❌ Erro ao conectar ao Supabase: {e}")
        print("\n💡 Dica: Verifique se a senha do banco está correta e se a porta/pooler está configurada.")
        return False

if __name__ == "__main__":
    test_connection()
