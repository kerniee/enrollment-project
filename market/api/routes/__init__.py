from .imports import router as import_router
from .nodes import router as nodes_router
from .delete import router as delete_router
from .sales import router as sales_router
from .node import router as node_router

ROUTERS = (import_router, nodes_router, delete_router, sales_router, node_router)
