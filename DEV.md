# Developer Documentation

## Project Structure

### Central API

This file contains all [decorest](https://github.com/bkryza/decorest) wrappers for the Central REST API. All APIs calls use those wrappers.

### Central Token Auth

This file handles the token exchange and authentication with Central. It extends `httpx.Auth`

### Communication

This folder will handle the communication with the enduser. Currently cli and websocket are supported.

### Helper

This folder contains the `ArubaSerial.py` module which can be used to validate if a given string is a valid Serial Number.

### GenericExcelHandler

This file is the generic version of the ExcelHandler. It is extended in the Modules.

### "Modules"

Every Module contains four type of files:

- Central*.py
- *Handler.py
- *ExcelHandler.py
- *WSHandler.py

#### Central*.py

This contains a statefull handler of all interaction with central. It caches data and tries to reduce the number of API calls.

#### *Handler.py

This contains the logic behind the module. It will interact with the user through the `*WSHandler.py`, write excel files via the `*ExcelHandler.py` and interact with Central through the `Central*.py`

#### *ExcelHandler.py

This implements the GenericExcelHandler with the data that we want to write for this module.

#### *WSHandler.py

This file creates the websocket endpoint and handles the sessions.
