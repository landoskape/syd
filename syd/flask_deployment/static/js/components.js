function updateParameter(name, value) {
    console.log(`Sending parameter update: ${name} = ${value}`);  // Debug log
    fetch('/update_parameter', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({name, value})
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error(`Error updating parameter: ${data.error}`);  // Debug log
            return;
        }
        console.log('Update successful, applying updates');  // Debug log
        // Update plot
        document.getElementById('plot').src = data.plot;
        // Apply any parameter updates
        for (const [param, js] of Object.entries(data.updates)) {
            console.log(`Applying update for ${param}`);  // Debug log
            eval(js);
        }
    })
    .catch(error => {
        console.error('Error in updateParameter:', error);  // Debug log
    });
}

function buttonClick(name) {
    fetch('/button_click', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({name})
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error(data.error);
            return;
        }
        // Update plot
        document.getElementById('plot').src = data.plot;
        // Apply any parameter updates
        for (const [param, js] of Object.entries(data.updates)) {
            eval(js);
        }
    });
}