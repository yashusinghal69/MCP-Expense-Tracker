import os
import random
import datetime
import dotenv
import asyncio
from typing import Dict, List
from supabase import create_client, Client 
from fastmcp import FastMCP
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

dotenv.load_dotenv()
 
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")  
Categorties_Path = os.path.join(os.path.dirname(__file__), 'catagories.json')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

mcp = FastMCP(name='Expense Tracker')


async def init_db() -> Dict[str, str]:
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS expenses (
        id BIGSERIAL PRIMARY KEY,
        date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        amount DECIMAL(10, 2) NOT NULL,
        category VARCHAR(255) NOT NULL,
        sub_category VARCHAR(255),
        note TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """

    def _sync_create():
        conn = psycopg2.connect(DATABASE_URL)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        cursor.execute(create_table_sql)
        cursor.close()
        conn.close()
        return {"status": "success", "message": "Expenses table created/verified successfully in Supabase PostgreSQL database"}

    try:
        return await asyncio.to_thread(_sync_create)
    except Exception as e:
        error_msg = f"Error creating table: {str(e)}"
        print(f"ERROR: {error_msg}")
        return {"status": "error", "message": error_msg}


@mcp.tool
async def add_expense(amount: float, category: str, sub_category: str = "", note: str = "", date: str = "") -> Dict[str, str]:
    """Add an expense to the database using Supabase official client (async wrapper)."""
    try:
        if not date:
            date = datetime.datetime.now().isoformat()

        data = {
            "date": date,
            "amount": amount,
            "category": category,
            "sub_category": sub_category,
            "note": note
        }

        def _sync_insert():
            return supabase.table("expenses").insert(data).execute()

        response = await asyncio.to_thread(_sync_insert)

        return {"status": "success", "message": "Expense added successfully", "id": str(response.data[0]["id"]) }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool
async def list_expenses(start_date: str = "", end_date: str = "", category: str = "", limit: int | None = None) -> List[dict]:
    """List expenses from the database using Supabase official client (async wrapper)."""
    def _sync_query():
        query = (
            supabase
            .table("expenses")
            .select("id, date, amount, category, sub_category, note")
        )

        if start_date:
            query = query.gte("date", start_date)
        if end_date:
            query = query.lte("date", end_date)
        if category:
            query = query.eq("category", category)

        query = query.order("date", desc=True)

        if limit is not None:
            query = query.limit(limit)

        return query.execute()

    try:
        response = await asyncio.to_thread(_sync_query)
        return response.data
    except Exception as e:
        return [{"error": str(e)}]


@mcp.resource('expenses://categories', mime_type='application/json')
async def categories():
    def _read():
        with open(Categorties_Path, 'r',encoding='utf-8') as f:
            return f.read()

    return await asyncio.to_thread(_read)

# test the server (MCP Inspector)-> uv run fastmcp dev main.py
# run the server -> uv run fastmcp run main.py
# Add server to cluade desktop -> uv run fastmcp install claude-desktop main.py
# you can convert fastAPI app directly in to FASTMCP   
# # also make an proxy server to connect claude-desktop to fastmcp server (in fastMCP)     
if __name__ == "__main__":
    asyncio.run(init_db())
    mcp.run(transport='http',host='0.0.0.0',port=8000)
