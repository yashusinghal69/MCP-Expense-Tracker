import os
import random
import datetime
import dotenv
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


 
def init_db() -> dict[str, str]:
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
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
        cursor.execute(create_table_sql)
        cursor.close()
        conn.close()

        return {"status": "success", "message": "Expenses table created/verified successfully in Supabase PostgreSQL database"}

    except Exception as e:
        error_msg = f"Error creating table: {str(e)}"
        print(f"ERROR: {error_msg}")
        return {"status": "error", "message": error_msg}

init_db() 

@mcp.tool
def add_expense(amount: float, category: str, sub_category: str = "", note: str = "", date: str = "") -> dict[str, str]:
    """Add an expense to the database using Supabase official client."""  
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
        
        response = supabase.table("expenses").insert(data).execute()
        
        return {"status": "success", "message": "Expense added successfully", "id": str(response.data[0]["id"])}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool
def list_expenses(start_date: str = "", end_date: str = "", category: str = "", limit: int | None = None) -> list[dict]:
    """List expenses from the database using Supabase official client, most recent first. Can filter by date range and/or category. Returns full list by default if limit is not specified."""
    try:
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
        
        response = query.execute()
        
        return response.data
    except Exception as e:
        return [{"error": str(e)}]


@mcp.resource('expenses://categories', mime_type='application/json')
def categories():
    
    with open(Categorties_Path, 'r',encoding='utf-8') as f:
        return f.read()

# test the server (MCP Inspector)-> uv run fastmcp dev main.py
# run the server -> uv run fastmcp run main.py
# Add server to cluade desktop -> uv run fastmcp install claude-desktop main.py
# you can convert fastAPI app directly in to FASTMCP        
if __name__ == "__main__":
     mcp.run(transport='http',host='0.0.0.0',port=8000)
