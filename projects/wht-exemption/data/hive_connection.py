import os
from pyhive import hive

def get_hive_connection():
    auth_mode = os.getenv("HIVE_AUTH")

    connection_args = dict(
        host=os.getenv("HIVE_HOST"),
        port=int(os.getenv("HIVE_PORT")),
        username=os.getenv("HIVE_USERNAME"),
        database=os.getenv("HIVE_DATABASE"),
        auth=auth_mode,
        configuration={
            "transportMode": "http",
            "httpPath": os.getenv("HIVE_HTTP_PATH")
        }
    )

    if auth_mode in ["LDAP", "CUSTOM"]:
        connection_args["password"] = os.getenv("HIVE_PASSWORD")

    if auth_mode == "KERBEROS":
        connection_args["kerberos_service_name"] = os.getenv("HIVE_KERBEROS_SERVICE")

    return hive.Connection(**connection_args)