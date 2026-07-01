"""辩论 API 层 — 路由与 Pydantic schemas。"""

# routes 在 main.py 注册时延迟导入，避免循环依赖
__all__ = ["router"]


def _get_router():
    """延迟导入路由，避免路由初始化错误阻塞其他模块加载。"""
    from debate.api.routes import router
    return router