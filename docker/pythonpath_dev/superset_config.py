# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
# This file is included in the final Docker image and SHOULD be overridden when
# deploying the image to prod. Settings configured here are intended for use in local
# development environments. Also note that superset_config_docker.py is imported
# as a final step as a means to override "defaults" configured here
#
import logging
import os
from datetime import timedelta
from typing import Optional

from redis_cluster_cache import RedisClusterCache

from celery.schedules import crontab
from flask_appbuilder.security.manager import AUTH_OAUTH

logger = logging.getLogger()


def get_env_variable(var_name: str, default: Optional[str] = None) -> str:
    """Get the environment variable or raise exception."""
    try:
        return os.environ[var_name]
    except KeyError:
        if default is not None:
            return default
        else:
            error_msg = "The environment variable {} was missing, abort...".format(
                var_name
            )
            raise EnvironmentError(error_msg)


AUTH_TYPE = AUTH_OAUTH
AUTH_USER_REGISTRATION = True
AUTH_ROLE_ADMIN = "Admin"
AUTH_ROLE_PUBLIC = "Viewer"
AUTH_USER_REGISTRATION_ROLE = "Viewer"

OAUTH_PROVIDERS = [
    {
        "name": "google",
        "icon": "fa-google",
        "whitelist": "@brigad.co",
        "token_key": "access_token",
        "remote_app": {
            "api_base_url": "https://www.googleapis.com/oauth2/v2/",
            "client_kwargs": {"scope": "openid email profile"},
            "request_token_url": None,
            "access_token_url": "https://accounts.google.com/o/oauth2/token",
            "authorize_url": "https://accounts.google.com/o/oauth2/auth",
            "client_id": "265593737427-0iv8d4357n07i0escb4ht1rfnnospgdf.apps.googleusercontent.com",
            "client_secret": "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",
            "jwks_uri": "https://www.googleapis.com/oauth2/v3/certs",
        },
    }
]

DATABASE_DIALECT = get_env_variable("DATABASE_DIALECT")
DATABASE_USER = get_env_variable("DATABASE_USER")
DATABASE_PASSWORD = get_env_variable("DATABASE_PASSWORD")
DATABASE_HOST = get_env_variable("DATABASE_HOST")
DATABASE_PORT = get_env_variable("DATABASE_PORT")
DATABASE_DB = get_env_variable("DATABASE_DB")

# The SQLAlchemy connection string.
SQLALCHEMY_DATABASE_URI = "%s://%s:%s@%s:%s/%s" % (
    DATABASE_DIALECT,
    DATABASE_USER,
    DATABASE_PASSWORD,
    DATABASE_HOST,
    DATABASE_PORT,
    DATABASE_DB,
)

REDIS_HOST = get_env_variable("REDIS_HOST")
REDIS_PORT = get_env_variable("REDIS_PORT")
REDIS_PASSWORD = get_env_variable("REDIS_PASSWORD")

CELERY_REDIS_HOST = get_env_variable("CELERY_REDIS_BROKER_HOST", REDIS_HOST)
CELERY_BACKEND_DB = get_env_variable("CELERY_BACKEND_DB")
CELERY_REDIS_BACKEND_URL = get_env_variable(
    "CELERY_REDIS_BACKEND_URL", f"redis://{CELERY_REDIS_HOST}:{REDIS_PORT}/0"
)
CELERY_REDIS_PORT = get_env_variable("CELERY_REDIS_PORT", REDIS_PORT)
CELERY_BROKER_DB = get_env_variable("CELERY_BROKER_DB", "0")

GLOBAL_ASYNC_QUERIES_REDIS_HOST = get_env_variable("GLOBAL_ASYNC_QUERIES_REDIS_HOST")
GLOBAL_ASYNC_QUERIES_REDIS_DB = get_env_variable("GLOBAL_ASYNC_QUERIES_REDIS_DB")

RESULTS_BACKEND = RedisClusterCache(
    host=REDIS_HOST,
    port=6379,
    password=REDIS_PASSWORD,
    default_timeout=255,
    ssl=True,
    ssl_cert_reqs=None,
    socket_connect_timeout=3,
    socket_timeout=3,
)

CACHE_CONFIG = {
    "CACHE_TYPE": "RedisClusterCache",
    "CACHE_DEFAULT_TIMEOUT": 1500,
    "CACHE_KEY_PREFIX": "superset",
    "CACHE_REDIS_CLUSTER": f"{REDIS_HOST}:{REDIS_PORT}",
    "CACHE_REDIS_PASSWORD": REDIS_PASSWORD,
    "CACHE_OPTIONS": {
        "ssl": True,
        "ssl_cert_reqs": None,
        "socket_connect_timeout": 3,
        "socket_timeout": 3,
    },
}
DATA_CACHE_CONFIG = {**CACHE_CONFIG, "CACHE_KEY_PREFIX": "superset_data"}
FILTER_STATE_CACHE_CONFIG = {**CACHE_CONFIG, "CACHE_KEY_PREFIX": "superset_filter"}
EXPLORE_FORM_DATA_CACHE_CONFIG = {
    **CACHE_CONFIG,
    "CACHE_KEY_PREFIX": "superset_explore",
}


class CeleryConfig(object):
    broker_url = f"redis://{CELERY_REDIS_HOST}:{REDIS_PORT}/{CELERY_BROKER_DB}"
    imports = ("superset.sql_lab",)
    result_backend = f"db+postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}/{CELERY_BACKEND_DB}"
    worker_prefetch_multiplier = 1
    task_acks_late = False
    beat_schedule = {
        "reports.scheduler": {
            "task": "reports.scheduler",
            "schedule": crontab(minute="*", hour="*"),
        },
        "reports.prune_log": {
            "task": "reports.prune_log",
            "schedule": crontab(minute=10, hour=0),
        },
        "cache-warmup-hourly": {
            "task": "cache-warmup",
            "schedule": crontab(minute=1, hour="*"),  # @hourly
            "kwargs": {
                "strategy_name": "top_n_dashboards",
                "top_n": 5,
                "since": "30 days ago",
            },
        },
    }


CELERY_CONFIG = CeleryConfig

EXTRA_CATEGORICAL_COLOR_SCHEMES = [
    {
        "id": "brigad_colors",
        "description": "",
        "label": "Brigad Viz categorical colors",
        "isDefault": True,
        "colors": [
            "#A71143",
            "#E82340",
            "#F87E79",
            "#666666",
            "#999999",
            "#CCCCCC",
            "#D94444",
            "#FBBCBC",
            "#FFB915",
            "#FFE2A1",
            "#14A984",
            "#8FEBD4",
            "#3AA3FF",
            "#9FD2FF",
        ],
    }
]

FEATURE_FLAGS = {
    "ALERT_REPORTS": True,
    "ENABLE_TEMPLATE_PROCESSING": True,
    "DASHBOARD_EDIT_CHART_IN_NEW_TAB": True,
    "DASHBOARD_CROSS_FILTERS": True,
    "SQL_VALIDATORS_BY_ENGINE": True,
    "DISABLE_LEGACY_DATASOURCE_EDITOR": True,
    # experimental
    "DASHBOARD_NATIVE_FILTERS": True,
    "DASHBOARD_RBAC": True,
    "DRILL_TO_DETAIL": True,
    "HORIZONTAL_FILTER_BAR": True,
    "GLOBAL_ASYNC_QUERIES": True,
    "DASHBOARD_FILTERS_EXPERIMENTAL": True,
}

GLOBAL_ASYNC_QUERIES_REDIS_CONFIG = {
    "port": 6379,
    "host": CELERY_REDIS_HOST,
    "db": GLOBAL_ASYNC_QUERIES_REDIS_DB,
    "ssl": False,
}

GLOBAL_ASYNC_QUERIES_REDIS_STREAM_PREFIX = "global_async"
GLOBAL_ASYNC_QUERIES_REDIS_STREAM_LIMIT = 1000
GLOBAL_ASYNC_QUERIES_REDIS_STREAM_LIMIT_FIREHOSE = 100000
GLOBAL_ASYNC_QUERIES_JWT_COOKIE_NAME = "async-token"
GLOBAL_ASYNC_QUERIES_JWT_COOKIE_SECURE = False
GLOBAL_ASYNC_QUERIES_JWT_COOKIE_DOMAIN = None
GLOBAL_ASYNC_QUERIES_JWT_SECRET = "15a9de40-e2ef-458e-bb38-7a212ae66e87"
GLOBAL_ASYNC_QUERIES_TRANSPORT = "polling"
GLOBAL_ASYNC_QUERIES_POLLING_DELAY = int(
    timedelta(milliseconds=500).total_seconds() * 1000
)

ALERT_REPORTS_NOTIFICATION_DRY_RUN = True
WEBDRIVER_BASEURL = "http://superset:8088/"
# The base URL for the email report hyperlinks.
WEBDRIVER_BASEURL_USER_FRIENDLY = WEBDRIVER_BASEURL

SQLLAB_CTAS_NO_LIMIT = True

#
# Optionally import superset_config_docker.py (which will have been included on
# the PYTHONPATH) in order to allow for local settings to be overridden
#
try:
    import superset_config_docker
    from superset_config_docker import *  # noqa

    logger.info(
        f"Loaded your Docker configuration at " f"[{superset_config_docker.__file__}]"
    )
except ImportError:
    logger.info("Using default Docker config...")
