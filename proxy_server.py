from fastmcp import FastMCP
from fastmcp.server.proxy import ProxyClient


# {
#   "mcpServers": {
#     "Expense Tracker": {
#       "command": "C:\\Users\\yashu\\.local\\bin\\uv.exe",
#       "args": [
#         "run",
#         "--project",
#         "E:\\MCP CampusX",
#         "fastmcp",
#         "run",
#         "E:\\MCP CampusX\\main.py"
#       ],
#       "env": {},
#       "cwd": "E:\\MCP CampusX"
#     }
#   }
# }

 
mcp = FastMCP.as_proxy(
    ProxyClient("https://mcp-expense-tracker-supabase.fastmcp.app/mcp"),
    name="Expense Tracker Proxy Server"
)

if __name__ == "__main__":
    mcp.run()
