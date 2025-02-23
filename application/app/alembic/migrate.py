from alembic import command
from alembic.config import Config
from pathlib import Path
import os


db_url = os.environ["CONNECTION_STRING"]
alembic_path = Path(__file__).parent / "alembic.ini"
migration_files_path = str(Path(__file__).parent)
alembic_config = Config(str(alembic_path))

alembic_config.set_main_option("sqlalchemy.url", db_url)
alembic_config.set_main_option("script_location", migration_files_path)

def upgrade():
    command.upgrade(alembic_config, "head")

if __name__ == "__main__":
    upgrade()
