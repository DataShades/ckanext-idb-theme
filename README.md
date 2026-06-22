[![Tests](https://github.com/DataShades/ckanext-idb-theme/workflows/Tests/badge.svg?branch=main)](https://github.com/DataShades/ckanext-idb-theme/actions)

# ckanext-idb-theme


## Requirements

If your extension works across different versions you can add the following table:

Compatibility with core CKAN versions:

| CKAN version    | Compatible?   |
| --------------- | ------------- |
| 2.9 and earlier | not tested    |
| 2.10            | not tested    |
| 2.11            | not tested    |



## Installation

To install ckanext-idb-theme:

1. Activate your CKAN virtual environment, for example:

     . /usr/lib/ckan/default/bin/activate

2. Clone the source and install it on the virtualenv

    git clone https://github.com/DataShades/ckanext-idb-theme.git
    cd ckanext-idb-theme
    pip install -e .
	pip install -r requirements.txt

3. Add `idb_theme theming` to the `ckan.plugins` setting in your CKAN
   config file (by default the config file is located at
   `/etc/ckan/default/ckan.ini`).





## Development

Watch styles and re-compile CSS on change:

```sh
make dev
```

Build production-ready styles:

```sh
make build
```

## Tests

To run the tests, do:

    pytest --ckan-ini=test.ini


## Releasing a new version of ckanext-idb-theme

If ckanext-idb-theme should be available on PyPI you can follow these steps to publish a new version:

1. Update the version number in the `pyproject.toml` file. See [PEP 440](http://legacy.python.org/dev/peps/pep-0440/#public-version-identifiers) for how to choose version numbers.

2. Make sure you have the latest version of necessary packages:

    pip install --upgrade setuptools wheel twine

3. Create a source and binary distributions of the new version:

       python -m build && twine check dist/*

   Fix any errors you get.

4. Upload the source distribution to PyPI:

       twine upload dist/*

5. Commit any outstanding changes:

       git commit -a
       git push

6. Tag the new release of the project on GitHub with the version number from
   the `setup.py` file. For example if the version number in `setup.py` is
   0.0.1 then do:

       git tag 0.0.1
       git push --tags

## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)
