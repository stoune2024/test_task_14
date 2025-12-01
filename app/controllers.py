from app.routers import crm_router


@crm_router.get("/")
async def main():
    return {"message": "Hello world!"}
