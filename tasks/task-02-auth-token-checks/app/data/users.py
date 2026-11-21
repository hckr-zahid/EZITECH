"""
LedgerPro Accountants - Task 2: User Store
Realistic accounting firm staff with hashed passwords and role assignments.
Roles: admin, auditor, accountant, viewer
No plaintext passwords stored anywhere.
"""

import bcrypt
from typing import Dict, Optional


def hash_password(plain: str) -> str:
    pwd_bytes = plain.encode("utf-8")[:72]
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    pwd_bytes = plain.encode("utf-8")[:72]
    hashed_bytes = hashed.encode("utf-8")
    return bcrypt.checkpw(pwd_bytes, hashed_bytes)


# In-memory user store - keyed by username.
# Passwords are bcrypt-hashed. Plaintext appears here only once
# (at seed time) so the store never holds a recoverable secret.
USERS: Dict[str, dict] = {
    "fatima.zahra": {
        "username": "fatima.zahra",
        "full_name": "Fatima Zahra",
        "email": "f.zahra@ledgerpro.com",
        "role": "admin",
        "department": "Administration",
        "hashed_password": hash_password("FatimaSecure#2026"),
        "disabled": False,
    },
    "tariq.mahmood": {
        "username": "tariq.mahmood",
        "full_name": "Tariq Mahmood",
        "email": "t.mahmood@ledgerpro.com",
        "role": "auditor",
        "department": "Statutory Audit & Assurance",
        "hashed_password": hash_password("TariqAudit@2026"),
        "disabled": False,
    },
    "zainab.ali": {
        "username": "zainab.ali",
        "full_name": "Zainab Ali",
        "email": "z.ali@ledgerpro.com",
        "role": "accountant",
        "department": "Tax Compliance & Advisory",
        "hashed_password": hash_password("ZainabTax!2026"),
        "disabled": False,
    },
    "bilal.khan": {
        "username": "bilal.khan",
        "full_name": "Bilal Khan",
        "email": "b.khan@ledgerpro.com",
        "role": "viewer",
        "department": "Client Relations",
        "hashed_password": hash_password("BilalView@2026"),
        "disabled": False,
    },
    "khalid.mansoor": {
        "username": "khalid.mansoor",
        "full_name": "Khalid Mansoor",
        "email": "k.mansoor@ledgerpro.com",
        "role": "accountant",
        "department": "Former Employee",
        "hashed_password": hash_password("OldPass#2024"),
        "disabled": True,  # deactivated account - must be blocked at login
    },
}


def get_user(username: str) -> Optional[dict]:
    return USERS.get(username)


def authenticate_user(username: str, password: str) -> Optional[dict]:
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user
