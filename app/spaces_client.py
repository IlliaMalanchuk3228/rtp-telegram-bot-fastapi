# app/spaces_client.py
import boto3
from botocore.client import Config
from datetime import date, timedelta
from app.config import settings
import json
from botocore.exceptions import ClientError

_session = boto3.session.Session()
_s3 = _session.client(
    "s3",
    region_name=settings.SPACES_REGION,
    endpoint_url=f"https://{settings.SPACES_REGION}.digitaloceanspaces.com",
    aws_access_key_id=settings.SPACES_KEY,
    aws_secret_access_key=settings.SPACES_SECRET,
    config=Config(signature_version="s3v4"),
)

_PLAY_URL_CACHE: str = None


def load_slot_metadata(lang: str) -> dict[str, dict]:
    """
    Fetches <lang>/metadata.json from Spaces and returns
    a mapping slot_name -> its metadata dict.
    """
    key = f"{lang}/metadata.json"
    try:
        resp = _s3.get_object(Bucket=settings.SPACES_NAME, Key=key)
    except ClientError:
        return {}
    body = resp["Body"].read()
    return json.loads(body)


def load_play_url() -> str:
    """
    Fetches (and caches) the one-play-url from config/play_url.txt
    in your Spaces bucket, so you can update it without a redeploy.
    """
    global _PLAY_URL_CACHE
    if _PLAY_URL_CACHE is None:
        obj = _s3.get_object(
            Bucket=settings.SPACES_NAME,
            Key="config/play_url.txt"
        )
        # read and strip any whitespace/newlines
        _PLAY_URL_CACHE = obj["Body"].read().decode("utf-8").strip()
    return _PLAY_URL_CACHE


def _list_for_stamp(lang: str, stamp: str) -> list[dict]:
    prefix = f"{lang}/"
    resp = _s3.list_objects_v2(Bucket=settings.SPACES_NAME, Prefix=prefix)

    slots = []
    for obj in resp.get("Contents", []):
        key = obj["Key"]  # e.g. "TR/dogs_20250517.png"
        filename = key.split("/", 1)[1]  # "dogs_20250517.png"
        if not filename.endswith(f"_{stamp}.png") and not filename.endswith(f"_{stamp}.jpg"):
            continue

        base = filename.rsplit("_", 1)[0]  # "dogs"
        name = base.replace("_", " ").title()
        # build URL from the dynamically derived property
        url = f"{settings.cdn_base}/{key}"
        slots.append({"name": name, "image": url})

    return slots


def list_today_slots(lang: str) -> list[dict]:
    """
    First try to list today’s slots; if none found, fall back to yesterday.
    """
    today = date.today()
    today_str = today.strftime("%Y%m%d")

    slots = _list_for_stamp(lang, today_str)
    if slots:
        return slots

    # fallback to yesterday
    yesterday = today - timedelta(days=1)
    yesterday_str = yesterday.strftime("%Y%m%d")
    return _list_for_stamp(lang, yesterday_str)
