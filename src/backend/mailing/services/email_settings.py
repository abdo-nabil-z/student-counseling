import base64
import hashlib
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken

from django.conf import settings
from django.core.mail import get_connection
from rest_framework.exceptions import ValidationError

from mailing.api_exceptions import EmailConnectionFailed, EmailSettingsNotConfigured
from mailing.models import EmailAccountSettings


@dataclass(frozen=True)
class ActiveEmailSettings:
    smtp_host: str
    smtp_port: int
    use_tls: bool
    smtp_username: str
    password: str
    from_name: str
    from_email: str
    persist_credentials: bool


def _fernet() -> Fernet:
    material = (
        getattr(settings, "EMAIL_CREDENTIALS_ENCRYPTION_KEY", "")
        or settings.SECRET_KEY
    )

    digest = hashlib.sha256(material.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def _encrypt_password(password: str) -> str:
    return _fernet().encrypt(password.encode()).decode()


def _decrypt_password(value: str) -> str:
    try:
        return _fernet().decrypt(value.encode()).decode()
    except (InvalidToken, ValueError) as exc:
        raise EmailSettingsNotConfigured(
            message=(
                "The saved email password could not be decrypted. "
                "Re-enter the email credentials."
            )
        ) from exc


def _runtime_file() -> Path:
    return Path(settings.EMAIL_RUNTIME_CREDENTIALS_FILE)


def _clear_runtime_file() -> None:
    try:
        _runtime_file().unlink()
    except FileNotFoundError:
        pass


def _write_runtime_settings(config: ActiveEmailSettings) -> None:
    path = _runtime_file()
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = asdict(config)
    payload["password"] = _encrypt_password(config.password)
    payload["persist_credentials"] = False

    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload), encoding="utf-8")
    os.chmod(temporary, 0o600)

    os.replace(temporary, path)
    os.chmod(path, 0o600)


def _read_runtime_settings() -> ActiveEmailSettings | None:
    path = _runtime_file()

    if not path.exists():
        return None

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))

        return ActiveEmailSettings(
            smtp_host=payload["smtp_host"],
            smtp_port=int(payload["smtp_port"]),
            use_tls=bool(payload["use_tls"]),
            smtp_username=payload["smtp_username"],
            password=_decrypt_password(payload["password"]),
            from_name=payload["from_name"],
            from_email=payload["from_email"],
            persist_credentials=False,
        )
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        _clear_runtime_file()
        return None


def _read_persistent_settings() -> ActiveEmailSettings | None:
    saved = EmailAccountSettings.objects.filter(pk=1).first()

    if saved is None:
        return None

    return ActiveEmailSettings(
        smtp_host=saved.smtp_host,
        smtp_port=saved.smtp_port,
        use_tls=saved.use_tls,
        smtp_username=saved.smtp_username,
        password=_decrypt_password(saved.encrypted_password),
        from_name=saved.from_name,
        from_email=saved.from_email,
        persist_credentials=True,
    )


def get_active_email_settings() -> ActiveEmailSettings:
    config = _read_runtime_settings() or _read_persistent_settings()

    if config is None:
        raise EmailSettingsNotConfigured()

    return config


def get_public_email_settings() -> dict:
    try:
        config = get_active_email_settings()
    except EmailSettingsNotConfigured:
        return {
            "smtp_host": settings.EMAIL_HOST,
            "smtp_port": settings.EMAIL_PORT,
            "use_tls": settings.EMAIL_USE_TLS,
            "smtp_username": "",
            "from_name": getattr(settings, "EMAIL_FROM_NAME", ""),
            "from_email": settings.DEFAULT_FROM_EMAIL,
            "persist_credentials": False,
            "password_configured": False,
        }

    return {
        "smtp_host": config.smtp_host,
        "smtp_port": config.smtp_port,
        "use_tls": config.use_tls,
        "smtp_username": config.smtp_username,
        "from_name": config.from_name,
        "from_email": config.from_email,
        "persist_credentials": config.persist_credentials,
        "password_configured": bool(config.password),
    }


def save_email_settings(data: dict) -> dict:
    try:
        current = get_active_email_settings()
    except EmailSettingsNotConfigured:
        current = None

    password = data.get("password", "")

    if not password and current is not None:
        password = current.password

    if not password:
        raise ValidationError({
            "password": [
                "A password is required because no saved password exists."
            ]
        })

    config = ActiveEmailSettings(
        smtp_host=data["smtp_host"],
        smtp_port=data["smtp_port"],
        use_tls=data["use_tls"],
        smtp_username=data["smtp_username"],
        password=password,
        from_name=data["from_name"],
        from_email=data["from_email"],
        persist_credentials=data["persist_credentials"],
    )

    if config.persist_credentials:
        EmailAccountSettings.objects.update_or_create(
            pk=1,
            defaults={
                "smtp_host": config.smtp_host,
                "smtp_port": config.smtp_port,
                "use_tls": config.use_tls,
                "smtp_username": config.smtp_username,
                "encrypted_password": _encrypt_password(config.password),
                "from_name": config.from_name,
                "from_email": config.from_email,
            },
        )

        _clear_runtime_file()

    else:
        EmailAccountSettings.objects.filter(pk=1).delete()
        _write_runtime_settings(config)

    return get_public_email_settings()


def clear_email_settings() -> None:
    EmailAccountSettings.objects.filter(pk=1).delete()
    _clear_runtime_file()


def build_email_connection(config=None):
    config = config or get_active_email_settings()

    return get_connection(
        backend=settings.EMAIL_BACKEND,
        host=config.smtp_host,
        port=config.smtp_port,
        username=config.smtp_username,
        password=config.password,
        use_tls=config.use_tls,
        timeout=settings.EMAIL_TIMEOUT,
        fail_silently=False,
    )


def test_active_email_connection() -> None:
    connection = build_email_connection()

    try:
        connection.open()
    except Exception as exc:
        raise EmailConnectionFailed(
            details={"reason": str(exc)}
        ) from exc
    finally:
        try:
            connection.close()
        except Exception:
            pass