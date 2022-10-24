# Central Device Lifecycle Tool

Tool to handle task relating to de-/comissioning of devices and upgrading firmware.

## Requirements + Environment Setup

Check for python using `python` or `python3`. Python3.x is required.

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
python -m install -r requirements
```

## Usage

### Simple

`python automation_web.py`

### Web

`python automation_web.py --web`

## Screenshots (Web)

![Wait for update to complete](./screenshots/Firmware/Wait.png)
![Device not known in Central](./screenshots/Firmware/NotInCentral.png)
![Device not known in Central - Refresh List drilldown](./screenshots/Firmware/NotInCentralDrillDown.png)
![Serial Number invalid](./screenshots/Firmware/Serial.png)
![Drilldown for device upgrade state](./screenshots/Firmware/DrillDown.png)
