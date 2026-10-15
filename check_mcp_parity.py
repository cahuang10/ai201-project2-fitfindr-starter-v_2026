from tools import search_listings
from mcp_client import call_tool

cases = [
    # normal match with a price ceiling
    {"description": "vintage graphic tee", "size": None, "max_price": 30.0},
    # size filter, including a "/" label like S/M
    {"description": "mesh top", "size": "M", "max_price": None},
    # shoe size with the US prefix
    {"description": "platform sneakers", "size": "US 8", "max_price": None},
    # nothing matches → should be []
    {"description": "designer ballgown", "size": "XXS", "max_price": 5.0},
    # only filler words → should be []
    {"description": "something for me", "size": None, "max_price": None},
]

for args in cases:
    direct = search_listings(**args)
    via_mcp = call_tool("search_listings", args)
    status = "SAME" if direct == via_mcp else "DIFFERENT"
    print(f"{status:9} direct={len(direct):2}  mcp={len(via_mcp):2}  {args}")