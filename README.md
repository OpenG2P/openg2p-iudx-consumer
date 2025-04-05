# OpenG2P IUDX Consumer
[![Pre-commit Status](https://github.com/OpenG2P/openg2p-iudx-consumer/actions/workflows/pre-commit.yml/badge.svg?branch=develop)](https://github.com/OpenG2P/openg2p-iudx-consumer/actions/workflows/pre-commit.yml?query=branch%3Adevelop)
[![Build Status](https://github.com/OpenG2P/openg2p-iudx-consumer/actions/workflows/test.yml/badge.svg?branch=develop)](https://github.com/OpenG2P/openg2p-iudx-consumer/actions/workflows/test.yml?query=branch%3Adevelop)
[![codecov](https://codecov.io/gh/OpenG2P/openg2p-iudx-consumer/branch/develop/graph/badge.svg)](https://codecov.io/gh/OpenG2P/openg2p-iudx-consumer)
[![openapi](https://img.shields.io/badge/open--API-swagger-brightgreen)](https://validator.swagger.io/?url=https://raw.githubusercontent.com/OpenG2P/openg2p-iudx-consumer/develop/api-docs/generated/openapi.json)
[![PyPI](https://img.shields.io/pypi/v/openg2p-iudx-consumer?label=pypi%20package)](https://pypi.org/project/openg2p-iudx-consumer)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/openg2p-iudx-consumer)](https://pypi.org/project/openg2p-iudx-consumer)

Sample implementation of a Consumer for IUDX Data Exchange Framework.

## Developer Notes

### Run with Docker

- Subscribe to OpenG2P Registry related resources in IUDX Catalogue.
- Create a file `.env` with the following and edit with appropriate values.
  ```
  IUDX_CONSUMER_CONSUMER_CLIENT_ID="consumerClientId"
  IUDX_CONSUMER_CONSUMER_CLIENT_SECRET="consumerClientSecret"
  IUDX_CONSUMER_RESOURCE_QUEUE_NAMES='["consumerId/demographic-data","consumerId/land-info","consumerId/crop-info","consumerId/income-details"]'
  IUDX_CONSUMER_RESOURCE_IDS='["uuid1","uuid2","uuid3","uuid4"]'
  IUDX_CONSUMER_ATTR_SEARCH_API_URL=""
  IUDX_CONSUMER_TOKEN_API_URL=""
  # IUDX_CONSUMER_AMQP_HOST=""
  # IUDX_CONSUMER_AMQP_PORT=""
  IUDX_CONSUMER_AMQP_USERNAME=""
  IUDX_CONSUMER_AMQP_PASSWORD=""
  ```
- Run
  ```sh
  docker compose up -d
  ```
- Open opensearch-dashboards UI and got to Saved Objects menu [http://localhost:5601/app/management/opensearch-dashboards/objects](http://localhost:5601/app/management/opensearch-dashboards/objects). And Upload dashboards given in [dashboards](./dashboards) directory.
- Then access the UI at [http://localhost:8000](http://localhost:8000).

### Run without Docker (for development)

- Subscribe in IUDX and create `.env` as given in above method.
- Run only opensearch and dashboards services with docker compose.
  ```sh
  docker compose up -d opensearch
  docker compose up -d opensearch-dashboards
  ```
- Create python virtual env and install python module.
  ```sh
  python3 -m venv .venv
  . .venv/bin/activate
  pip install -e .
  ```
- Run
  ```sh
  . .venv/bin/activate
  ./main.py run
  ```

## Licenses

This repository is licensed under [MPL-2.0](LICENSE).
