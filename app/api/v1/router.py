from fastapi import APIRouter

from app.api.v1 import admin, auth, catalog, explore, matches, templates, user_cards

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(catalog.router)
api_router.include_router(user_cards.router)
api_router.include_router(user_cards.pending_router)
api_router.include_router(explore.router)
api_router.include_router(matches.router)
api_router.include_router(templates.router)
