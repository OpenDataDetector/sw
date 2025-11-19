#!/usr/bin/env python3
"""Test script to debug OCI registry access"""

# /// script
# requires-python = ">= 3.10"
# dependencies = [
#   "opencontainers",
#   "requests",
#   "rich"
# ]
# ///

import sys
from rich.console import Console
from opencontainers.distribution.reggie import (
    NewClient,
    WithUsernamePassword,
    WithDebug,
    WithName,
    WithReference,
)

console = Console()


def test_registry_access(
    registry_url: str,
    repo: str,
    tag: str,
    username: str = "",
    password: str = "",
):
    """Test if we can access a registry and fetch a manifest"""

    console.print(f"[bold]Testing registry access[/bold]")
    console.print(f"Registry: {registry_url}")
    console.print(f"Repository: {repo}")
    console.print(f"Tag: {tag}")
    console.print(f"Username: {username if username else '[dim]<empty>[/dim]'}")
    console.print(f"Password: {'***' if password else '[dim]<empty>[/dim]'}")
    console.print()

    try:
        # Create client
        console.print("[bold]Creating registry client...[/bold]")
        client = NewClient(
            registry_url,
            WithUsernamePassword(username, password),
            WithDebug(True),
        )

        # Try to fetch manifest
        console.print(f"[bold]Fetching manifest for {repo}:{tag}...[/bold]")
        req = (
            client.NewRequest(
                "GET",
                "/v2/<name>/manifests/<reference>",
                WithName(repo),
                WithReference(tag),
            ).SetHeader("Accept", "application/vnd.oci.image.manifest.v1+json")
        )

        resp = client.Do(req)
        resp.raise_for_status()

        manifest = resp.json()

        console.print("[green]✓ Successfully fetched manifest![/green]")
        console.print(f"Schema version: {manifest.get('schemaVersion')}")
        console.print(f"Media type: {manifest.get('mediaType')}")
        console.print(f"Number of layers: {len(manifest.get('layers', []))}")

        return True

    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        console.print_exception()
        return False


if __name__ == "__main__":
    import os

    # Test the base image from the user's command
    success = test_registry_access(
        registry_url="https://ghcr.io",
        repo="acts-project/ubuntu2404",
        tag="82",
        username=os.environ.get("REGISTRY_USERNAME", ""),
        password=os.environ.get("REGISTRY_PASSWORD", ""),
    )

    sys.exit(0 if success else 1)
