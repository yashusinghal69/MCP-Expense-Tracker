from fastmcp import FastMCP


mcp = FastMCP.as_proxy(
    'https://mcp-expense-tracker-supabase.fastmcp.app/mcp',
    name = 'Expense Tracker Proxy Server',
)

if __name__ == "__main__":
    mcp.run()