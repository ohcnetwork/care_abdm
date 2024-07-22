# Care Abdm

[![Release Status](https://img.shields.io/pypi/v/care_abdm.svg)](https://pypi.python.org/pypi/care_abdm)
[![Build Status](https://github.com/coronasafe/care_abdm/actions/workflows/build.yaml/badge.svg)](https://github.com/coronasafe/care_abdm/actions/workflows/build.yaml)

Care Abdm is a plugin for care to add voice auto fill support using external services like OpenAI whisper and Google Speech to Text.

## Features

- Voice auto fill support for care
- Support for OpenAI whisper and Google Speech to Text

## Installation

https://care-be-docs.coronasafe.network/pluggable-apps/configuration.html

https://github.com/coronasafe/care/blob/develop/plug_config.py

To install care abdm, you can add the plugin config in [care/plug_config.py](https://github.com/coronasafe/care/blob/develop/plug_config.py) as follows:

```python
...

abdm_plug = Plug(
    name="abdm",
    package_name="git+https://github.com/coronasafe/care_abdm.git",
    version="@master",
    configs={
        "ABDM_CLIENT_ID": "abdm_client_id",
        "ABDM_CLIENT_SECRET": "abdm_client_secret",
        "ABDM_URL": "",
        "HEALTH_SERVICE_API_URL": "",
        "ABDM_FACILITY_URL": "",
        "HIP_NAME_PREFIX": "",
        "HIP_NAME_SUFFIX": "",
        "ABDM_USERNAME": "",
        "X_CM_ID": "",
        "FIDELIUS_URL": "",
        "AUTH_USER_MODEL": "users.User"
    },
)
plugs = [abdm_plug]
...
```

## Configuration

The following configurations variables are available for Care Abdm:

- `ABDM_CLIENT_ID`: The client id for the ABDM service.
- `ABDM_CLIENT_SECRET`: The client secret for the ABDM service.
- `ABDM_URL`: The URL for the ABDM service APIs.
- `HEALTH_SERVICE_API_URL`: The URL for the health service APIs.
- `ABDM_FACILITY_URL`: The URL for the ABDM facility APIs.
- `HIP_NAME_PREFIX`: The prefix for the HIP name. Used to avoid conflicts while registering a facility as ABDM health facility.
- `HIP_NAME_SUFFIX`: The suffix for the HIP name. Used to avoid conflicts while registering a facility as ABDM health facility.
- `ABDM_USERNAME`: The internal username for the ABDM service. Intended to track the records created via ABDM.
- `X_CM_ID`: The X-CM-ID header value for the ABDM service.
- `FIDELIUS_URL`: The URL for the Fidelius service. Used for encryption and decryption of data from and to ABDM.
- `AUTH_USER_MODEL`: The user model to use for the ABDM service.

The plugin will try to find the API key from the config first and then from the environment variable.

## License

This project is licensed under the terms of the [MIT license](LICENSE).

---

This plugin was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) using the [coronasafe/care-plugin-cookiecutter](https://github.com/coronasafe/care-plugin-cookiecutter).
