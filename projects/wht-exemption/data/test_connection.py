"""Script to test Hive connection. Run from this directory: python test_connection.py"""
from dotenv import load_dotenv

load_dotenv()

from hive_connection import get_hive_connection
import pandas as pd

conn = get_hive_connection()
