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
    name="gn_plugin_depobio",
    version=version,
    description="PluginDepobio",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    maintainer="Parcs nationaux des Écrins et PATRINAT",
    maintainer_email="geonature@ecrins-parcnational.fr",
    url="https://github.com/PnX-SI/gn_plugin_depobio",
    packages=setuptools.find_packages("backend"),
    package_dir={"": "backend"},
    package_data={
        "gn_plugin_depobio": ["demarches_simplifiees/graphql/*.graphql"],
    },
    install_requires=requirements,
    entry_points={
        "gn_module": [
            "code = gn_plugin_depobio:MODULE_CODE",
            "picto = gn_plugin_depobio:MODULE_PICTO",
            "doc_url = gn_plugin_depobio:MODULE_DOC_URL",
            "blueprint = gn_plugin_depobio.blueprint:blueprint",
            "config_schema = gn_plugin_depobio.conf_schema_toml:GnModuleSchemaConf",
            "migrations = gn_plugin_depobio:migrations",
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
