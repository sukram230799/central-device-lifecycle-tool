const EMPTY_SERIAL = "---";
const STATUS_LIST = ['status-red', 'status-green', 'status-orange', 'status-grey'];

const snInput = document.getElementById('sn-input');
const unlicenseCheckBox = document.getElementById('unlicense-checkbox');
const submitButton = document.getElementById('submit-button');
const excelButton = document.getElementById('excel-button');

const serialBox = document.getElementById('sn-box');
const logBox = document.getElementById('log-box');
const statusBox = document.getElementById('status-box');

if (window.location.pathname.startsWith('/app/firmware/')) {
    firmware = true;
    decomission = false;
}
else if (window.location.pathname.startsWith('/app/decomission')) {
    decomission = true;
    firmware = false;
}

let socket;
if (firmware)
    socket = new WebSocket("ws://" + location.host + "/firmware/ws");
else if (decomission)
    socket = new WebSocket("ws://" + location.host + "/decomission/ws");

let downloaded = true;

socket.onopen = function (e) {
    socket.send(JSON.stringify({ type: 'status', value: 'connected' }));
};

socket.onmessage = function (event) {
    console.log(event.data);
    message = JSON.parse(event.data);

    switch (message.type) {
        case 'status':
            setStatus(message);
            downloaded = false;
            break;
        case 'log':
            appendLog(message);
            break;
        case 'clear':
            clear(message);
            break;
        case 'serial':
            setSerial(message);
            break;
        case 'excel':
            setExcel(message);
            break;
    }
};

function clear(message) {
    statusBox.classList.remove(...STATUS_LIST);
    statusBox.innerText = 'Status';
    serialBox.innerText = EMPTY_SERIAL;
    logBox.innerText = "";
}

function setStatus(message) {
    statusBox.classList.remove(...STATUS_LIST);
    switch (message.color) {
        case 'red':
            statusBox.classList.add('status-red');
            break;
        case 'green':
            statusBox.classList.add('status-green');
            break;
        case 'grey':
            statusBox.classList.add('status-grey');
            break;
        case 'orange':
            statusBox.classList.add('status-orange');
            break;
        default:
            statusBox.classList.add('status-red');
            break;
    }
    statusBox.innerText = message.value;
}

// Local display functions

function appendLog(message) {
    logBox.innerText += "\n" + message.value;
}

function setSerial(message) {
    serialNumber = message.value.trim();
    if (serialNumber === "")
        serialNumber = EMPTY_SERIAL;
    serialBox.innerText = serialNumber;
}

function setExcel(message) {
    excelFileName = message.value;
    excelButton.href = message.value;
}

// Websocket close and error handling

socket.onclose = function (event) {
    clear();
    setStatus({ value: 'DISCONNECTED', color: 'red' });
    if (event.wasClean) {
        log(`[close] Connection closed cleanly, code=${event.code} reason=${event.reason}`);
    } else {
        // e.g. server process killed or network down
        // event.code is usually 1006 in this case
        log('[close] Connection died');
    }
};

socket.onerror = function (error) {
    appendLog(error.message);
    log(`[error] ${error.message}`);
};

// Serial number handling

function submitSerial() {
    sendSerial(snInput.value);
    snInput.value = "";
}

function sendSerial(serial) {
    console.log(serial);
    message = { type: 'serial', value: serial }
    if (decomission)
        message.unlicense = unlicenseCheckBox.checked;
    socket.send(JSON.stringify(message));
}

// Eventlisteners

snInput.addEventListener("keypress", function (event) {
    if (event.key === "Enter") {
        event.preventDefault();

        submitSerial();
    }
});

submitButton.addEventListener("click", (event) => {
    submitSerial();
});

excelButton.addEventListener("click", (event) => {
    downloaded = true;
});

window.addEventListener('beforeunload', function (e) {
    if (!downloaded) {
        e.returnValue = 'Test';
        e.preventDefault();
    }
});

