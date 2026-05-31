import sqlglot
import sqlglot.expressions as exp

from core.exceptions import SQLValidationError


def validate_sql(sql: str) -> str:
    """Valide que le SQL est un SELECT pur — rejette tout le reste.

    Seule protection applicative. La vraie défense est :
    genbi_readonly (SELECT-only) + RLS PostgreSQL.

    Retourne le SQL nettoyé si valide.
    Lève SQLValidationError sinon.
    """
    sql = sql.strip()

    if not sql:
        raise SQLValidationError("Le SQL ne peut pas être vide.")

    try:
        statements = sqlglot.parse(sql, dialect="postgres")
    except sqlglot.errors.ParseError as e:
        raise SQLValidationError(f"SQL invalide : {e}") from e

    if not statements:
        raise SQLValidationError("Aucune instruction SQL détectée.")

    if len(statements) > 1:
        raise SQLValidationError(
            "Une seule instruction SELECT est autorisée. "
            "Les instructions multiples (injection par ';') sont interdites."
        )

    statement = statements[0]

    if not isinstance(statement, exp.Select):
        kind = type(statement).__name__
        raise SQLValidationError(
            f"Opération interdite : '{kind}'. Seules les requêtes SELECT sont autorisées."
        )

    return sql
