"""Add depobio module permission

Revision ID: 1e2926e0b603
Revises: 78ba67f597ee
Create Date: 2025-08-28 18:55:23.047899

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "01eb67fd7851"
down_revision = None
branch_labels = ("plugin_depobio",)
depends_on = ("f051b88a57fd",)  # geonature: creation of gn_permissions.t_permissions_available

module_code = "PLUGIN_DEPOBIO"
object_code = "ALL"
action_code = "R"


def upgrade():
    op.execute(
        f"""
        INSERT INTO
            gn_permissions.t_permissions_available (
                id_module,
                id_object,
                id_action,
                label,
                scope_filter
            )
        SELECT
            m.id_module,
            o.id_object,
            a.id_action,
            v.label,
            v.scope_filter
        FROM
            (
                VALUES
                    ('{module_code}', '{object_code}', '{action_code}', False, 'Accéder au module')
            ) AS v (module_code, object_code, action_code, scope_filter, label)
        JOIN
            gn_commons.t_modules m ON m.module_code = v.module_code
        JOIN
            gn_permissions.t_objects o ON o.code_object = v.object_code
        JOIN
            gn_permissions.bib_actions a ON a.code_action = v.action_code
        """
    )


def downgrade():
    op.execute(
        f"""
        DELETE FROM gn_permissions.t_permissions_available
        WHERE
            id_module = (
                SELECT id_module
                FROM gn_commons.t_modules
                WHERE module_code = '{module_code}')
            AND id_object = (
                SELECT id_object
                FROM gn_permissions.t_objects
                WHERE code_object = '{object_code}')
            AND id_action = (
                SELECT id_action
                FROM gn_permissions.bib_actions
                WHERE code_action = '{action_code}');
        """
    )
