# How to Contribute

* Reach out to us on our public [Slack channel](https://www.wavefront.com/join-public-slack).
* If you run into any issues, let us know by creating a GitHub issue.

## Testing

We have a handful of GitHub actions to check code and run tests, but most of our testbed consists of Python [unittest](https://docs.python.org/3/library/unittest.html). Please write Python [unittest](https://docs.python.org/3/library/unittest.html#basic-example) for new code you create.

## Submitting changes

* When submitting changes, be sure to increment the **version** number in [setup.py](setup.py).
  The version number is documented as such in setup.py.
* We follow [semantic versioning](https://semver.org/).
* For bug fixes, increment the patch version (last number).
* For backward compatible changes to the API, update the minor version (second number), and zero out the patch version.
* For breaking changes to the API, increment the major version (first number) and zero out the minor and patch versions.

## Coding conventions

Start reading our code and you'll get the hang of it. We use linters and the following and code checks:

* Install Linters

    ```bash
    python -m pip install -U flake8 flake8-colors
    python -m pip install -U flake8-import-order pep8-naming
    python -m pip install -U pydocstyle pylint
    ```

* Install Extra Dependencies

    ```bash
    python -m pip install -U Deprecated requests tdigest
    ```

* Run Flake8 Checks

    ```bash
    python -m flake8
    ```

* Run PyLint Checks

    ```bash
    python -m pylint -d duplicate-code wavefront_sdk
    ```

* Run PyDocStyle

    ```bash
    python -m pydocstyle
    ```

* Execute Unit Tests

    ```bash
    python -m unittest discover
    ```
