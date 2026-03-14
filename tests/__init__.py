import os

# Our reporter tests expect english language column names.
# The reporter module gets the language from the environment.
# This code gets run before any test code is run, and any module is loaded
# It's a clean solution to our problem (other solutions involve module reloading
# and other shenanigans)
os.environ["LANGUAGE"] = "en"
