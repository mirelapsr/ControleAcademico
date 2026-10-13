"""
auth.py — CAMADA DE AUTENTICAÇÃO
================================
Responsável por:
    - Hash e verificação de senhas (bcrypt).
    - Emissão e validação de tokens JWT (PyJWT).
    - Dependência `get_usuario_atual`, usada nas rotas protegidas para
      extrair o usuário autenticado a partir do header Authorization.
"""

import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

import db

# ---------------------------------------------------------------------------
# CONFIGURAÇÃO
# ---------------------------------------------------------------------------

SECRET_KEY = os.getenv("SECRET_KEY", "chave_secreta_desenvolvimento_2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

_HASH_FALSO = bcrypt.hashpw(
    b"senha_impossivel_de_existir_2026", bcrypt.gensalt()
).decode("utf-8")


# ---------------------------------------------------------------------------
# SENHAS
# ---------------------------------------------------------------------------

def hash_senha(senha: str) -> str:
    """Gera o salt e devolve o hash bcrypt da senha, em UTF-8."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(senha.encode("utf-8"), salt).decode("utf-8")


def verificar_senha(senha: str, hash_salvo: str) -> bool:
    """Compara a senha em texto puro com o hash salvo, de forma segura
    (comparação em tempo constante feita internamente pelo bcrypt)."""
    try:
        return bcrypt.checkpw(senha.encode("utf-8"), hash_salvo.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------------------------
# TOKEN JWT
# ---------------------------------------------------------------------------

def criar_token(id_usuario: int, papel: str) -> tuple[str, int]:
    """Gera um token JWT assinado para o usuário informado.

    Retorna a tupla (token_jwt, tempo_em_segundos_ate_expirar).
    """
    agora = datetime.now(timezone.utc)
    expira_em = agora + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(id_usuario),
        "papel": papel,
        "iat": agora,
        "exp": expira_em,
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    tempo_em_segundos = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    return token, tempo_em_segundos


# ---------------------------------------------------------------------------
# DEPENDÊNCIA DE AUTENTICAÇÃO
# ---------------------------------------------------------------------------

_CREDENCIAIS_INVALIDAS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Token inválido ou expirado.",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_usuario_atual(token: str = Depends(oauth2_scheme)) -> dict:
    """Decodifica o JWT recebido, valida assinatura/expiração e devolve o
    usuário correspondente, já carregado do banco.

    Usada como dependência (`Depends(get_usuario_atual)`) em qualquer rota
    que exija um usuário autenticado e ativo.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise _CREDENCIAIS_INVALIDAS

    id_usuario_str = payload.get("sub")
    if id_usuario_str is None:
        raise _CREDENCIAIS_INVALIDAS

    try:
        id_usuario = int(id_usuario_str)
    except (TypeError, ValueError):
        raise _CREDENCIAIS_INVALIDAS

    usuario = db.buscar_usuario(id_usuario)
    if usuario is None:
        raise _CREDENCIAIS_INVALIDAS

    if not usuario.get("ativo"):
        raise _CREDENCIAIS_INVALIDAS

    return usuario
