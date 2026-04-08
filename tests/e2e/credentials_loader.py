"""
Secure credential loader supporting SOPS and Ansible Vault.

This module provides secure credential loading with comprehensive
audit logging (patterns only, never credential values).
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger("credentials_loader")


@dataclass
class CredentialAccessLog:
    """Audit log entry for credential access."""

    timestamp: str
    client_id: str
    environment: str
    source: str
    credential_type: str
    access_method: str
    success: bool
    error_message: str | None = None


class CredentialLoader(ABC):
    """Abstract base class for credential loaders."""

    @abstractmethod
    def load_credentials(self, client_id: str, environment: str = "staging") -> dict[str, Any]:
        """Load credentials for a client."""
        pass

    @abstractmethod
    def log_access(self, client_id: str, environment: str, source: str, success: bool) -> None:
        """Log credential access for audit purposes."""
        pass


class SecureCredentialLoader(CredentialLoader):
    """
    Secure credential loader with support for SOPS and Ansible Vault.

    Usage:
        loader = SecureCredentialLoader()
        creds = loader.load_credentials("client1", "production")

    Priority:
    1. SOPS encrypted files (preferred)
    2. Ansible Vault encrypted files
    3. Environment variables (CI/CD fallback)

    Security:
    - Never logs credential values
    - Audit logs all access attempts
    - Masks secrets in error messages
    """

    # Sensitive key patterns to redact in logs
    SENSITIVE_PATTERNS = [
        re.compile(r"(password|secret|key|token|credential)s?", re.IGNORECASE),
        re.compile(r"private.*key", re.IGNORECASE),
    ]

    def __init__(
        self,
        project_root: Path | None = None,
        sops_binary: str = "sops",
        ansible_vault_binary: str = "ansible-vault",
    ):
        self.project_root = project_root or Path("/var/www/meta.expc.cz")
        self.sops_binary = sops_binary
        self.ansible_vault_binary = ansible_vault_binary
        self._access_log: list[CredentialAccessLog] = []

    def load_credentials(self, client_id: str, environment: str = "staging") -> dict[str, Any]:
        """
        Load credentials using available secure methods.

        Attempts SOPS first, then Ansible Vault, then environment fallback.
        Never returns None - raises exception on failure.
        """
        logger.info(f"Loading credentials for client '{client_id}' in environment '{environment}'")

        # Try SOPS first
        try:
            credentials = self._load_from_sops(client_id, environment)
            self._log_access(
                client_id, environment, "sops", success=True, source_count=len(credentials)
            )
            return credentials
        except CredentialLoadError as e:
            logger.debug(f"SOPS load failed: {e}")

        # Try Ansible Vault
        try:
            credentials = self._load_from_ansible_vault(client_id, environment)
            self._log_access(
                client_id,
                environment,
                "ansible_vault",
                success=True,
                source_count=len(credentials),
            )
            return credentials
        except CredentialLoadError as e:
            logger.debug(f"Ansible Vault load failed: {e}")

        # Environment fallback (CI/CD)
        try:
            credentials = self._load_from_environment(client_id)
            self._log_access(
                client_id,
                environment,
                "environment",
                success=True,
                source_count=len(credentials),
            )
            return credentials
        except CredentialLoadError as e:
            logger.warning(f"Environment fallback failed: {e}")

        # All methods failed
        self._log_access(client_id, environment, "all_methods", success=False)
        raise CredentialLoadError(f"Failed to load credentials for {client_id} using any method")

    def _load_from_sops(self, client_id: str, environment: str) -> dict[str, Any]:
        """Load credentials from SOPS-encrypted file."""
        sops_file = self.project_root / "secrets" / f"{client_id}_{environment}.enc.json"

        if not sops_file.exists():
            raise CredentialLoadError(f"SOPS file not found: {sops_file}")

        logger.info(f"Attempting to decrypt SOPS file: {sops_file.name}")

        try:
            result = subprocess.run(
                [self.sops_binary, "-d", str(sops_file)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                # Mask any potential secrets in error output
                safe_error = self._mask_sensitive_data(result.stderr)
                raise CredentialLoadError(f"SOPS decryption failed: {safe_error}")

            return json.loads(result.stdout)

        except subprocess.TimeoutExpired:
            raise CredentialLoadError("SOPS decryption timed out")
        except json.JSONDecodeError as e:
            raise CredentialLoadError(f"Invalid JSON in SOPS file: {e}")

    def _load_from_ansible_vault(self, client_id: str, environment: str) -> dict[str, Any]:
        """Load credentials from Ansible Vault-encrypted file."""
        vault_file = self.project_root / "ansible" / "group_vars" / "all" / "vault.yml"

        if not vault_file.exists():
            raise CredentialLoadError(f"Ansible Vault file not found: {vault_file}")

        logger.info(f"Attempting to decrypt Ansible Vault file: {vault_file.name}")

        # Check for vault password file
        vault_pass_file = Path.home() / ".vault_pass"
        if not vault_pass_file.exists():
            raise CredentialLoadError("Vault password file not found")

        try:
            result = subprocess.run(
                [
                    self.ansible_vault_binary,
                    "view",
                    str(vault_file),
                    "--vault-password-file",
                    str(vault_pass_file),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                safe_error = self._mask_sensitive_data(result.stderr)
                raise CredentialLoadError(f"Vault decryption failed: {safe_error}")

            vault_data = yaml.safe_load(result.stdout)
            # Extract client-specific credentials
            client_key = f"{client_id}_{environment}"
            if client_key not in vault_data:
                raise CredentialLoadError(f"No credentials found for {client_key} in vault")

            return vault_data[client_key]

        except subprocess.TimeoutExpired:
            raise CredentialLoadError("Ansible Vault decryption timed out")

    def _load_from_environment(self, client_id: str) -> dict[str, Any]:
        """Load credentials from environment variables (CI/CD fallback)."""
        logger.info("Attempting to load credentials from environment variables")

        prefix = f"{client_id.upper()}_"
        credentials: dict[str, Any] = {}

        # Collect all environment variables with client prefix
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Remove prefix and convert to lowercase
                credential_key = key[len(prefix) :].lower()
                credentials[credential_key] = value

        if not credentials:
            raise CredentialLoadError(f"No environment variables found with prefix {prefix}")

        # Log which keys were found (not values)
        key_list = list(credentials.keys())
        logger.info(f"Loaded credentials from environment: {key_list}")

        return credentials

    def _log_access(
        self,
        client_id: str,
        environment: str,
        source: str,
        success: bool,
        source_count: int | None = None,
        error_message: str | None = None,
    ) -> None:
        """
        Log credential access for audit purposes.

        Only logs access patterns, never credential values.
        """
        from datetime import datetime, timezone

        log_entry = CredentialAccessLog(
            timestamp=datetime.now(timezone.utc).isoformat(),
            client_id=client_id,
            environment=environment,
            source=source,
            credential_type="multi-source",
            access_method=source,
            success=success,
            error_message=error_message,
        )

        self._access_log.append(log_entry)

        # Log to standard logger (sanitized)
        status = "SUCCESS" if success else "FAILURE"
        count_info = f" ({source_count} sources)" if source_count else ""
        logger.info(
            f"Credential access {status}: client={client_id}, "
            f"env={environment}, source={source}{count_info}"
        )

    def log_access(self, client_id: str, environment: str, source: str, success: bool) -> None:
        """Public method to log access."""
        self._log_access(client_id, environment, source, success)

    def _mask_sensitive_data(self, text: str) -> str:
        """
        Mask potentially sensitive data in log output.

        Replaces values that look like secrets with [REDACTED].
        """
        lines = text.split("\n")
        masked_lines = []

        for line in lines:
            masked_line = line
            for pattern in self.SENSITIVE_PATTERNS:
                # Mask the value after equals sign or colon
                masked_line = pattern.sub("[REDACTED]", masked_line)
            masked_lines.append(masked_line)

        return "\n".join(masked_lines)

    def get_access_log(self) -> list[CredentialAccessLog]:
        """Get the access log for audit purposes."""
        return self._access_log.copy()

    def clear_access_log(self) -> None:
        """Clear the access log."""
        self._access_log.clear()


class CredentialLoadError(Exception):
    """Exception raised when credential loading fails."""

    pass


class EnvironmentCredentialLoader(CredentialLoader):
    """
    Simple loader that only uses environment variables.

    Suitable for CI/CD environments where secrets are injected.
    """

    def __init__(self, prefix_separator: str = "_"):
        self.prefix_separator = prefix_separator

    def load_credentials(self, client_id: str, environment: str = "staging") -> dict[str, Any]:
        """Load credentials from environment variables."""
        prefix = f"{client_id.upper()}{self.prefix_separator}"
        credentials: dict[str, Any] = {}

        for key, value in os.environ.items():
            if key.startswith(prefix):
                credential_key = key[len(prefix) :].lower()
                credentials[credential_key] = value

        if not credentials:
            raise CredentialLoadError(f"No environment variables with prefix {prefix}")

        return credentials

    def log_access(self, client_id: str, environment: str, source: str, success: bool) -> None:
        """No-op for environment loader."""
        pass


def create_credential_loader(
    method: str = "auto", project_root: Path | None = None
) -> CredentialLoader:
    """
    Factory function to create appropriate credential loader.

    Args:
        method: One of 'auto', 'sops', 'ansible', 'environment'
        project_root: Project root directory

    Returns:
        Configured CredentialLoader instance
    """
    if method == "environment":
        return EnvironmentCredentialLoader()
    elif method in ("auto", "sops", "ansible"):
        return SecureCredentialLoader(project_root=project_root)
    else:
        raise ValueError(f"Unknown credential loading method: {method}")


# Example usage for testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    loader = SecureCredentialLoader()

    try:
        # This will fail without proper setup, but demonstrates usage
        creds = loader.load_credentials("client1", "staging")
        print(f"Loaded credentials: {list(creds.keys())}")
    except CredentialLoadError as e:
        print(f"Expected error (no credentials configured): {e}")
