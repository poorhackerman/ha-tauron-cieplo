"""Constants for TAURON Ciepło."""

DOMAIN = "tauron_cieplo"
CONF_CITY = "city"
NAME = "TAURON Ciepło"
BASE_URL = "https://cieplo.tauron.pl"
SOURCE_URL = f"{BASE_URL}/wylaczenia-i-awarie"
CONF_STREET = "street"
CONF_STREET_ID = "street_id"
CONF_UPDATE_INTERVAL = "update_interval"
DEFAULT_UPDATE_INTERVAL = 60
RETRY_UPDATE_INTERVAL = 5
MIN_UPDATE_INTERVAL = 5
MAX_UPDATE_INTERVAL = 1440
