"""
db_utils.py — Utilitários compartilhados entre os scripts de ETL.
"""

from __future__ import annotations

import os
from typing import Any
import pyodbc
from dotenv import load_dotenv
from loguru import logger
from sqlalchemy import create_engine
from pathlib import Path 
import sys
import socket
import psycopg2


# Caminho padrão do .env em todos os ambientes do projeto
_DOTENV_PATH = os.path.join(os.path.expanduser("~"), "secure", "env", ".env")


def carregar_env(chaves: list[str], dotenv_path: str = _DOTENV_PATH) -> dict[str, str]:
    """
    Carrega o .env e valida que todas as *chaves* estão presentes e não vazias.
    Lança EnvironmentError com a lista dos ausentes se alguma faltar.

    Uso:
        env = carregar_env([
            "prd_dw_database", "dw_username", "dw_password",
            "dw_dsn", "dw_driver", "password_engine",
        ])
    """
    load_dotenv(dotenv_path)

    valores = {k: os.getenv(k) for k in chaves}
    ausentes = [k for k, v in valores.items() if not v]

    if ausentes:
        raise EnvironmentError(
            f"Variáveis de ambiente obrigatórias não definidas: {', '.join(ausentes)}"
        )

    return valores  # type: ignore[return-value]  # ausentes já filtrou None


def conectar_sql_server(
    server: str,
    driver: str,
    username: str,
    password: str,
    password_engine: str,
    database: str,
) -> tuple[pyodbc.Connection, pyodbc.Cursor, Any]:
    """
    Abre conexão pyodbc + SQLAlchemy engine para SQL Server.
    Lança ConnectionError em caso de falha de interface.
    """
    try:
        conn = pyodbc.connect(
            f"SERVER={server};DATABASE={database};"
            f"UID={username};PWD={password};DRIVER={driver}"
        )
        conn_str = (
            f"DRIVER={driver};SERVER={server};DATABASE={database};"
            f"UID={username};PWD={password_engine}"
        )
        engine = create_engine(
            f"mssql+pyodbc:///?odbc_connect={conn_str}",
            fast_executemany=True,
        )
        return conn, conn.cursor(), engine
    except (pyodbc.InterfaceError, pyodbc.OperationalError) as exc:
        raise ConnectionError(f"Falha na conexão com '{database}' em '{server}'") from exc


def configurar_logger(nome_rotina: str, nivel_log: str = "INFO") -> None:
    """
    Configura o Loguru para gravar logs em arquivos diários dentro da pasta 'rotinas'.
    Garante a rotação diária e captura automaticamente exceções não tratadas (ex: falhas no crontab).
    """

    dir_logs = Path.home() / "rotinas" / nome_rotina / "logs"
    dir_logs.mkdir(parents=True, exist_ok=True)

    arquivo_log = dir_logs / f"{nome_rotina}.log"

    logger.remove()

    logger.add(
        arquivo_log,
        rotation="04:00",
        retention="30 days",
        # compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        level=nivel_log,
        enqueue=True
    )

    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
        level=nivel_log
    )


def conectar_postgres(
        host: str,
        username: str,
        password: str,
        database: str,
        port: str = "5432"
) -> tuple[Any, Any, Any]:
    """
    Abre conexão com o PostgreSQL
    """

    try: 
        conn = psycopg2.connect(
            host = host,
            database = database,
            user = username,
            password = password,
            port = port
        )

        engine_url = f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"
        engine = create_engine(engine_url)

        return conn, conn.cursor(), engine 

    except Exception as e:
        logger.error(f"Falha na conexão com o PostgreSQL '{database}' em '{host}': {e}" )
        raise ConnectionError(f"Falha na conexão com o PostgreSQL '{database}' em '{host}'") from e