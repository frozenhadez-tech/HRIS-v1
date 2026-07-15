"""Vercel serverless entrypoint.

Vercel's @vercel/python runtime serves the WSGI `app` exported here.
All routes are rewritten to this function (see vercel.json).
"""
import os
import sys

# make the Flask app package importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from app import app  # noqa: E402  (Flask WSGI application)
