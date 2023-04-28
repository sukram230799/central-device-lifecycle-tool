# Central Device Lifecycle Tool

Tool to handle tasks relating to upgrading firmware and de-/comissioning of devices.

## Requirements + Environment Setup

Check for python using `python --version` or `python3 --version`. Python3.x is required and must be installed in the path.

Git is also needed for a custom library to handle the API calls to central. Screenshots for the install can be found [here](./INSTALL.md)

### Easy Setup + Start

Use `setup.bat` to setup environment (Python in path required). Use `start-web.bat` to start the app and configure credentials.

### Virtual Environment

Create virtualenv to install project dependencies only for this project

``` sh
python -m virtualenv venv
```

### Before each start

Activate the created environment before each usage

#### Windows + Powershell

``` powershell
& .\venv\Scripts\Activate.ps
```

#### Windows + CMD

``` cmd
call venv/Scripts/activate
```

#### Linux

``` sh
source ./venv/bin/activate
```

## Install

``` sh
python -m pip install -r requirements.txt
```

## Usage

### Access Token + Endpoint

#### Endpoint

![Endpoint](./screenshots/Central/Endpoint.png)

#### Credentials

![Credentials](./screenshots/Central/Credentials.png)

#### endpoint.json

``` json
{
    "name": "Central",
    "base_url": "https://...-apigw.central.arubanetworks.com"
}
```

#### credential.json

``` json
{
    "access_token": "8nQ...",
    "appname": "nms",
    "authenticated_userid": "user.name@example.com",
    "created_at": 1663245291,
    "credential_id": "a7c...",
    "expires_in": 7200,
    "id": "6f6...",
    "refresh_token": "Paa...",
    "scope": "all",
    "token_type": "bearer"
}

```

#### client_id.json

``` json
{
    "client_id": "xDj...",
    "client_secret": "H05..."
}
```

### Simple

`python automation_web.py`

### Web

`python automation_web.py --web`

## Screenshots (Web)

### Wait for update to complete

![Wait for update to complete](./screenshots/Firmware/Wait.png)

### Device (currently) not known in Central

![Device not known in Central](./screenshots/Firmware/NotInCentral.png)

### Device not known. Second scan, refresh gateway

![Device not known in Central - Refresh List drilldown](./screenshots/Firmware/NotInCentralDrillDown.png)

### Invalid Serial Number

![Serial Number invalid](./screenshots/Firmware/Serial.png)

### Drilldown for device upgrade state

![Drilldown for device upgrade state](./screenshots/Firmware/DrillDown.png)
