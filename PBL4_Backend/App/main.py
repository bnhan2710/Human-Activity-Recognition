from .config import settings
from .db import Base, engine
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .model.user_model import User
from .model.activity_model import Activity
from .model.notification_model import Notification
from .controllers import auth_controller
from .controllers import activity_controller
from .controllers import notification_controller

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Hoặc ["http://localhost:59904"] để an toàn hơn
    allow_credentials=True,
    allow_methods=["*"],  # Cho phép POST, GET, OPTIONS, v.v.
    allow_headers=["*"],
)
app.include_router(auth_controller.router)
app.include_router(activity_controller.router)
app.include_router(notification_controller.router)
Base.metadata.create_all(bind=engine)
@app.get("/")
def home():
    return {"app_name": settings.APP_NAME}
