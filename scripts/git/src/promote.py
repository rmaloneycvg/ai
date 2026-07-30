"""Manual environment promotion trigger (dev → staging → prod)."""

import click


@click.command()
@click.option("--from", "from_env", type=click.Choice(["dev", "staging"]), required=True, help="Source environment.")
@click.option("--to", "to_env", type=click.Choice(["staging", "prod"]), required=True, help="Target environment.")
@click.option("--dry-run", is_flag=True, help="Show what would happen without promoting.")
def main(from_env: str, to_env: str, dry_run: bool) -> None:
    """Manually promote code between environments via fast-forward merge."""
    # Validate promotion direction
    valid_promotions = {"dev": "staging", "staging": "prod"}
    if valid_promotions.get(from_env) != to_env:
        click.echo(f"❌ Invalid promotion: '{from_env}' → '{to_env}'. Valid: dev→staging, staging→prod.")
        raise SystemExit(1)

    if dry_run:
        click.echo(f"[DRY RUN] Would fast-forward '{to_env}' to match '{from_env}'.")
        raise SystemExit(0)

    # TODO: Implement fast-forward promotion
    click.echo(f"Promotion '{from_env}' → '{to_env}' — full implementation pending.")


if __name__ == "__main__":
    main()
