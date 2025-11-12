import os, time, uuid
import boto3
from datetime import datetime, timedelta, timezone

region = os.getenv("AWS_REGION","us-east-2")
dynamodb = boto3.resource("dynamodb", region_name=region)
users_tbl = dynamodb.Table(os.getenv("DDB_USERS_TABLE","retro_users"))
sess_tbl  = dynamodb.Table(os.getenv("DDB_SESSIONS_TABLE","retro_sessions"))
TTL_MIN = int(os.getenv("SESSION_TTL_MINUTES","5"))

def now_utc(): return datetime.now(timezone.utc)

def create_user(username, password_hash, role="user"):
    ts = now_utc().isoformat()
    users_tbl.put_item(Item={
        "username": username, "password_hash": password_hash,
        "role": role, "created_at": ts, "last_login": None
    })

def get_user(username):
    return users_tbl.get_item(Key={"username": username}).get("Item")

def upsert_session(username):
    # Si existe sesión activa -> rechazar
    cur = sess_tbl.get_item(Key={"username": username}).get("Item")
    if cur and cur.get("expires_at",0) > int(time.time()):
        return None
    sid = str(uuid.uuid4())
    exp = int((now_utc() + timedelta(minutes=TTL_MIN)).timestamp())
    sess_tbl.put_item(Item={
        "username": username, "session_id": sid,
        "created_at": now_utc().isoformat(),
        "expires_at": exp
    })
    return {"session_id": sid, "expires_at": exp}

def touch_session(username):
    exp = int((now_utc() + timedelta(minutes=TTL_MIN)).timestamp())
    sess_tbl.update_item(
        Key={"username": username},
        UpdateExpression="SET expires_at=:e",
        ExpressionAttributeValues={":e": exp}
    )

def end_session(username):
    sess_tbl.delete_item(Key={"username": username})
