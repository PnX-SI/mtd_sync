import setuptools
from pathlib import Path


root_dir = Path(__file__).absolute().parent
with (root_dir / "VERSION").open() as f:
    version = f.read()
with (root_dir / "README.md").open() as f:
    long_description = f.read()
with (root_dir / "requirements.in").open() as f:
    requirements = f.read().splitlines()


setuptools.setup(
    name="mtd_sync",
    version=version,
    description="SynchronisationMTD",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    maintainer="Parcs nationaux des Écrins et PATRINAT",
    maintainer_email="geonature@ecrins-parcnational.fr",
    url="https://github.com/PnX-SI/mtd_sync",
    packages=setuptools.find_packages("src"),
    package_dir={"": "src"},
    install_requires=requirements,
    entry_points={
        "gn_module": [
            "code = mtd_sync:MODULE_CODE",
            "picto = mtd_sync:MODULE_PICTO",
            "doc_url = mtd_sync:MODULE_DOC_URL",
            "blueprint = mtd_sync.blueprint:blueprint",
            "config_schema = mtd_sync.conf_schema_toml:GnModuleSchemaConf",
            "tasks = mtd_sync.tasks",
            # "migrations = mtd_sync:migrations",
        ],
    },
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3"
        "Operating System :: OS Independent",
    ],
)
