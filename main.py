from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2AuthorizationCodeBearer
import httpx
import os
import json
from pathlib import Path
from starlette.middleware.sessions import SessionMiddleware
from datetime import datetime
import asyncio
from discord import HTTPException as DiscordHTTPException
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")
DISCORD_API_URL = os.getenv("DISCORD_API_URL")
BOT_TOKEN = os.getenv("BOT_TOKEN")
PREFIXES_FILE = Path(os.getenv("PREFIXES_FILE"))

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(SessionMiddleware, secret_key=DISCORD_CLIENT_SECRET)
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

STATS = {
    "start_time": datetime.now(),
    "total_visits": 0,
    "active_users": 0
}

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="https://discord.com/oauth2/authorize",
    tokenUrl="https://discord.com/api/oauth2/token",
)


async def get_guild_channels(guild_id: str, bot_token: str):
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bot {bot_token}"}
        response = await client.get(f"{DISCORD_API_URL}/guilds/{guild_id}/channels", headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch guild channels")
        return [ch for ch in response.json() if ch["type"] == 0]


def load_guild_channels():
    settings_file = Path("json/guild_settings.json")
    if settings_file.exists():
        with open(settings_file, encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_guild_settings():
    settings_file = Path("json/guild_settings.json")
    if settings_file.exists():
        with open(settings_file, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_guild_settings(data):
    settings_file = Path("json/guild_settings.json")
    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


async def log_settings_change(guild_id: str, action: str, user_id: str, bot_token: str):
    settings = load_guild_settings()
    guild_settings = settings.get(guild_id, {})
    mod_channel_id = guild_settings.get("mod_channel_id")
    if not mod_channel_id:
        return

    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bot {bot_token}", "Content-Type": "application/json"}
        embed = {
            "title": "Изменение настроек",
            "color": 0xFF0000,
            "timestamp": datetime.now().isoformat(),
            "fields": [
                {"name": "Действие", "value": action, "inline": False},
                {"name": "Пользователь", "value": f"<@{user_id}>", "inline": False},
            ],
        }
        payload = {"embeds": [embed]}
        try:
            await client.post(
                f"{DISCORD_API_URL}/channels/{mod_channel_id}/messages",
                headers=headers,
                json=payload,
            )
        except Exception as e:
            print(f"Ошибка логирования изменений в канал {mod_channel_id}: {e}")


def get_prefixes():
    if PREFIXES_FILE.exists():
        with open(PREFIXES_FILE) as f:
            return json.load(f)
    return {}


def save_prefixes(data):
    with open(PREFIXES_FILE, "w") as f:
        json.dump(data, f, indent=4)


async def get_user_guilds(access_token: str):
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await client.get(f"{DISCORD_API_URL}/users/@me/guilds", headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch user guilds")
        return response.json()


async def get_bot_guilds():
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bot {BOT_TOKEN}"}
        response = await client.get(f"{DISCORD_API_URL}/users/@me/guilds", headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch bot guilds")
        return [g["id"] for g in response.json()]


async def get_user_info(access_token: str):
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await client.get(f"{DISCORD_API_URL}/users/@me", headers=headers)
        if response.status_code != 200:
            return None
        return response.json()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    STATS["total_visits"] += 1
    return templates.TemplateResponse("index.html", {"request": request, "client_id": DISCORD_CLIENT_ID})


@app.get("/login")
async def login():
    return RedirectResponse(
        f"https://discord.com/oauth2/authorize?"
        f"client_id={DISCORD_CLIENT_ID}&"
        f"redirect_uri={DISCORD_REDIRECT_URI}&"
        f"response_type=code&"
        f"scope=identify%20guilds"
    )


@app.get("/auth")
async def auth_callback(code: str, request: Request):
    async with httpx.AsyncClient() as client:
        data = {
            "client_id": DISCORD_CLIENT_ID,
            "client_secret": DISCORD_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": DISCORD_REDIRECT_URI,
            "scope": "identify guilds"
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        token_response = await client.post(
            f"{DISCORD_API_URL}/oauth2/token",
            data=data,
            headers=headers
        )
        token_data = token_response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to get access token")

        request.session["access_token"] = access_token
        STATS["active_users"] += 1

        return RedirectResponse(url="/dashboard")


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    access_token = request.session.get("access_token")
    if not access_token:
        return RedirectResponse(url="/")

    try:
        user_info = await get_user_info(access_token)
        if not user_info:
            return RedirectResponse(url="/")

        user_guilds = await get_user_guilds(access_token)

        bot_guilds = await get_bot_guilds()

        managed_guilds = []
        unmanaged_guilds = []

        for guild in user_guilds:
            permissions = int(guild.get("permissions", 0))
            if permissions & 0x8:
                guild_data = {
                    "id": guild["id"],
                    "name": guild["name"],
                    "icon": guild.get("icon", "")
                }

                if guild["id"] in bot_guilds:
                    managed_guilds.append(guild_data)
                else:
                    unmanaged_guilds.append(guild_data)

        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "user": user_info,
                "managed_guilds": managed_guilds,
                "unmanaged_guilds": unmanaged_guilds,
                "client_id": DISCORD_CLIENT_ID
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/guild/{guild_id}", response_class=HTMLResponse)
async def guild_settings(request: Request, guild_id: str):
    prefixes = get_prefixes()
    current_prefix = prefixes.get(guild_id, "r!")
    settings = load_guild_settings().get(guild_id, {
        "administrators": [],
        "moderators": [],
        "mod_channel_id": None,
        "system_channel_id": None,
        "embed_message_id": None,
        "warning_types": [],
        "warning_limits": {},
        "warnings": [],
    })

    return templates.TemplateResponse(
        "guild.html",
        {
            "request": request,
            "guild_id": guild_id,
            "current_prefix": current_prefix,
            "settings": settings
        }
    )


@app.get("/guild/{guild_id}/channels")
async def get_channels(guild_id: str, request: Request):
    """Получение списка текстовых каналов сервера."""
    access_token = request.session.get("access_token")
    if not access_token:
        logger.error(f"No access token for guild_id={guild_id}")
        return RedirectResponse(url="/")

    try:
        user_guilds = await get_user_guilds(access_token)
        guild = next((g for g in user_guilds if g["id"] == guild_id), None)
        if not guild:
            logger.error(f"Guild {guild_id} not found in user guilds")
            raise HTTPException(status_code=403, detail="Guild not found")
        if not (int(guild["permissions"]) & 0x8):
            logger.error(f"User not admin for guild_id={guild_id}")
            raise HTTPException(status_code=403, detail="You are not an administrator of this guild")

        channels = await get_guild_channels(guild_id, BOT_TOKEN)
        logger.info(f"Successfully fetched channels for guild_id={guild_id}")
        return {"channels": channels}
    except HTTPException as e:
        logger.error(f"HTTP error for guild_id={guild_id}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error for guild_id={guild_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to fetch channels: {str(e)}")

@app.post("/guild/{guild_id}/settings")
async def update_guild_settings(guild_id: str, request: Request):
    access_token = request.session.get("access_token")
    if not access_token:
        return RedirectResponse(url="/")

    try:
        user_guilds = await get_user_guilds(access_token)
        guild = next((g for g in user_guilds if g["id"] == guild_id), None)
        if not guild or not (int(guild["permissions"]) & 0x8):
            raise HTTPException(status_code=403, detail="You are not an administrator of this guild")

        user_info = await get_user_info(access_token)
        if not user_info:
            return RedirectResponse(url="/")

        form_data = await request.form()
        mod_channel_id = form_data.get("mod_channel_id")
        system_channel_id = form_data.get("system_channel_id")
        admin_ids = form_data.get("admin_ids", "").split(",")
        mod_ids = form_data.get("mod_ids", "").split(",")

        if mod_channel_id:
            channels = await get_guild_channels(guild_id, BOT_TOKEN)
            if not any(ch["id"] == mod_channel_id for ch in channels):
                raise HTTPException(status_code=400, detail="Invalid mod channel ID")
        if system_channel_id:
            channels = await get_guild_channels(guild_id, BOT_TOKEN)
            if not any(ch["id"] == system_channel_id for ch in channels):
                raise HTTPException(status_code=400, detail="Invalid system channel ID")

        admin_ids = [id.strip() for id in admin_ids if id.strip().isdigit()]
        mod_ids = [id.strip() for id in mod_ids if id.strip().isdigit()]

        settings = load_guild_settings()
        if guild_id not in settings:
            settings[guild_id] = {
                "administrators": [],
                "moderators": [],
                "mod_channel_id": None,
                "system_channel_id": None,
                "embed_message_id": None,
                "warning_types": [],
                "warning_limits": {},
                "warnings": [],
            }

        changes = []
        if mod_channel_id and settings[guild_id]["mod_channel_id"] != int(mod_channel_id):
            settings[guild_id]["mod_channel_id"] = int(mod_channel_id)
            changes.append(f"Канал логов изменен на <#{mod_channel_id}>")
        if system_channel_id and settings[guild_id]["system_channel_id"] != int(system_channel_id):
            settings[guild_id]["system_channel_id"] = int(system_channel_id)
            changes.append(f"Системный канал изменен на <#{system_channel_id}>")
        if admin_ids != settings[guild_id]["administrators"]:
            settings[guild_id]["administrators"] = admin_ids
            changes.append(f"Список администраторов обновлен: {', '.join(f'<@{id}>' for id in admin_ids)}")
        if mod_ids != settings[guild_id]["moderators"]:
            settings[guild_id]["moderators"] = mod_ids
            changes.append(f"Список модераторов обновлен: {', '.join(f'<@{id}>' for id in mod_ids)}")

        if changes:
            save_guild_settings(settings)
            await log_settings_change(guild_id, "\n".join(changes), user_info["id"], BOT_TOKEN)
            return RedirectResponse(url=f"/guild/{guild_id}?success=true", status_code=303)
        else:
            return RedirectResponse(url=f"/guild/{guild_id}?no_changes=true", status_code=303)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/guild/{guild_id}/prefix")
async def update_prefix(guild_id: str, request: Request):
    form_data = await request.form()
    new_prefix = form_data.get("prefix")

    if not new_prefix:
        raise HTTPException(status_code=400, detail="Prefix is required")

    prefixes = get_prefixes()
    prefixes[guild_id] = new_prefix
    save_prefixes(prefixes)

    return RedirectResponse(url=f"/guild/{guild_id}?success=true", status_code=303)


@app.get("/stats", response_class=HTMLResponse)
async def stats_page(request: Request):
    uptime = datetime.now() - STATS["start_time"]
    hours, remainder = divmod(uptime.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"

    return templates.TemplateResponse(
        "stats.html",
        {
            "request": request,
            "total_visits": STATS["total_visits"],
            "active_users": STATS["active_users"],
            "uptime": uptime_str,
            "start_time": STATS["start_time"].strftime("%Y-%m-%d %H:%M:%S")
        }
    )