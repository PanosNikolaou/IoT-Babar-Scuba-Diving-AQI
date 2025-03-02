// Custom plugin for gradient background
const backgroundPlugin = {
    id: 'customBackground',
    beforeDraw: (chart) => {
        const { ctx, chartArea } = chart;
        if (!chartArea) {
            // Skip if chartArea is not yet defined
            return;
        }
        ctx.save();
        // Create a vertical gradient background
        const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
        gradient.addColorStop(0, '#e0f7fa'); // Light blue
        gradient.addColorStop(1, '#ffffff'); // White

        // Draw the gradient background
        ctx.fillStyle = gradient;
        ctx.fillRect(chartArea.left, chartArea.top, chartArea.width, chartArea.height);
        ctx.restore();
    },
};

const mqCtx = document.getElementById('mqChart').getContext('2d');
const mqChart = new Chart(mqCtx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [
            { label: 'Temperature', data: [], borderColor: 'rgba(255, 99, 132, 1)', backgroundColor: 'rgba(255, 99, 132, 0.2)', fill: true },
            { label: 'Humidity', data: [], borderColor: 'rgba(54, 162, 235, 1)', backgroundColor: 'rgba(54, 162, 235, 0.2)', fill: true },
            { label: 'LPG', data: [], borderColor: 'rgba(75, 192, 192, 1)', backgroundColor: 'rgba(75, 192, 192, 0.2)', fill: true },
            { label: 'CO', data: [], borderColor: 'rgba(153, 102, 255, 1)', backgroundColor: 'rgba(153, 102, 255, 0.2)', fill: true },
            { label: 'Smoke', data: [], borderColor: 'rgba(255, 206, 86, 1)', backgroundColor: 'rgba(255, 206, 86, 0.2)', fill: true },
            { label: 'CO_MQ7', data: [], borderColor: 'rgba(75, 0, 130, 1)', backgroundColor: 'rgba(75, 0, 130, 0.2)', fill: true },
            { label: 'CH4', data: [], borderColor: 'rgba(255, 127, 80, 1)', backgroundColor: 'rgba(255, 127, 80, 0.2)', fill: true },
            { label: 'CO_MQ9', data: [], borderColor: 'rgba(34, 139, 34, 1)', backgroundColor: 'rgba(34, 139, 34, 0.2)', fill: true },
            { label: 'CO2', data: [], borderColor: 'rgba(128, 0, 128, 1)', backgroundColor: 'rgba(128, 0, 128, 0.2)', fill: true },
            { label: 'NH3', data: [], borderColor: 'rgba(255, 165, 0, 1)', backgroundColor: 'rgba(255, 165, 0, 0.2)', fill: true },
            { label: 'NOx', data: [], borderColor: 'rgba(0, 128, 128, 1)', backgroundColor: 'rgba(0, 128, 128, 0.2)', fill: true },
            { label: 'Alcohol', data: [], borderColor: 'rgba(128, 128, 0, 1)', backgroundColor: 'rgba(128, 128, 0, 0.2)', fill: true },
            { label: 'Benzene', data: [], borderColor: 'rgba(255, 20, 147, 1)', backgroundColor: 'rgba(255, 20, 147, 0.2)', fill: true },
            { label: 'H2', data: [], borderColor: 'rgba(70, 130, 180, 1)', backgroundColor: 'rgba(70, 130, 180, 0.2)', fill: true },
            { label: 'Air', data: [], borderColor: 'rgba(220, 20, 60, 1)', backgroundColor: 'rgba(220, 20, 60, 0.2)', fill: true },
        ],
    },
    options: {
        responsive: true,
        scales: {
            x: { type: 'time', time: { unit: 'second' }, title: { display: true, text: 'Time' } },
            y: { title: { display: true, text: 'Value' } },
        },
    },
});

let mqCurrentPage = 1;
const mqRecordsPerPage = 10;
let activeFilter = '24hours'; // Default filter

document.getElementById('timeFilter').addEventListener('change', (event) => {
    activeFilter = event.target.value;
    document.getElementById('customDateRange').style.display = activeFilter === 'custom' ? 'block' : 'none';
});

document.getElementById('applyFilter').addEventListener('click', () => {
    fetchMqData(); // Re-fetch data with the selected filter
});

let mqData = []; // Global variable to store MQ sensor data

async function fetchMqData() {
    try {
        const response = await fetch('/api/mq-data');
        const result = await response.json();

        const mqData = result.mq_data || [];

        // Filter data based on selected criteria
        const filteredMqData = filterDataByCriteria(mqData);

        // Update the chart
        updateMqChart(filteredMqData);

        // Render the table and pagination
        renderMqTablePage(filteredMqData, mqCurrentPage);
        renderMqPaginationControls(filteredMqData);
    } catch (error) {
        console.error('Error fetching MQ data:', error);
    }
}

// Filter Data Based on User Selection
function filterDataByCriteria(data) {
    const now = new Date();
    let filteredData = data;

    if (activeFilter === '1hour') {
        const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);
        filteredData = data.filter(record => new Date(record.timestamp) >= oneHourAgo);
    } else if (activeFilter === '24hours') {
        const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
        filteredData = data.filter(record => new Date(record.timestamp) >= oneDayAgo);
    } else if (activeFilter === '7days') {
        const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        filteredData = data.filter(record => new Date(record.timestamp) >= sevenDaysAgo);
    } else if (activeFilter === 'custom') {
        const startDate = new Date(document.getElementById('startDate').value);
        const endDate = new Date(document.getElementById('endDate').value);
        filteredData = data.filter(record => {
            const recordDate = new Date(record.timestamp);
            return recordDate >= startDate && recordDate <= endDate;
        });
    }

    return filteredData;
}


function updateMqChart(filteredMqData) {
    //const MAX_DATA_POINTS = 50; // Optional: Limit the data points
    const maxDataPoints = parseInt(document.getElementById('maxDataPoints').value, 10) || 50;
    const sortedData = filteredMqData.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    const limitedData = sortedData.slice(0, maxDataPoints).reverse(); // Get the latest points in chronological order

    const timestamps = limitedData.map(record => new Date(record.timestamp));
    mqChart.data.labels = timestamps;

    mqChart.data.datasets.forEach((dataset) => {
        const key = dataset.label.replace(/ /g, '_');
        dataset.data = limitedData.map(record => record[key] || null);
    });

    mqChart.update();
}

document.getElementById('applyFilter').addEventListener('click', () => {
    const timeFilter = document.getElementById('timeFilter').value;
    const maxDataPoints = parseInt(document.getElementById('maxDataPoints').value, 10) || 50;
    let startDate = null;
    let endDate = new Date(); // Default to now

    if (timeFilter === 'custom') {
        startDate = new Date(document.getElementById('startDate').value);
        endDate = new Date(document.getElementById('endDate').value);
    } else if (timeFilter === '1hour') {
        startDate = new Date(endDate.getTime() - 60 * 60 * 1000);
    } else if (timeFilter === '24hours') {
        startDate = new Date(endDate.getTime() - 24 * 60 * 60 * 1000);
    } else if (timeFilter === '7days') {
        startDate = new Date(endDate.getTime() - 7 * 24 * 60 * 60 * 1000);
    }

    // Filter the global mqData variable
    const filteredData = mqData.filter(record => {
        const timestamp = new Date(record.timestamp);
        return (!startDate || timestamp >= startDate) && timestamp <= endDate;
    });

    // Limit the data to maxDataPoints
    const limitedData = filteredData.slice(-maxDataPoints);

    // Update the chart
    updateMqChart(limitedData);

    // Close the modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('filterModal'));
    modal.hide();
});

// Event listener for resetting the filter
document.getElementById('resetFilter').addEventListener('click', () => {
    document.getElementById('timeFilter').value = '24hours';
    document.getElementById('startDate').value = '';
    document.getElementById('endDate').value = '';
    document.getElementById('maxDataPoints').value = 50;

    // Reload the latest 50 data points
    const latestData = mqData.slice(-50);
    updateMqChart(latestData);
});

// Reset filter logic
document.getElementById('resetFilter').addEventListener('click', () => {
    document.getElementById('timeFilter').value = '24hours';
    document.getElementById('startDate').value = '';
    document.getElementById('endDate').value = '';
    document.getElementById('maxDataPoints').value = 50;

    // Reload the latest 50 data points
    const latestData = mqData.slice(-50);
    updateMqChart(latestData);
});


function renderMqTablePage(data, page) {
    const tableBody = document.getElementById('mq-data-table-body');
    tableBody.innerHTML = '';

    const startIndex = (page - 1) * mqRecordsPerPage;
    const endIndex = Math.min(startIndex + mqRecordsPerPage, data.length);
    const pageData = data.slice(startIndex, endIndex);

    pageData.forEach(record => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${new Date(record.timestamp).toLocaleString()}</td>
            <td>${record.temperature !== null ? record.temperature.toFixed(3) : 'N/A'}</td>
            <td>${record.humidity !== null ? record.humidity.toFixed(3) : 'N/A'}</td>
            <td>${record.LPG !== null ? record.LPG.toFixed(3) : 'N/A'}</td>
            <td>${record.CO !== null ? record.CO.toFixed(3) : 'N/A'}</td>
            <td>${record.Smoke !== null ? record.Smoke.toFixed(3) : 'N/A'}</td>
            <td>${record.CO_MQ7 !== null ? record.CO_MQ7.toFixed(3) : 'N/A'}</td>
            <td>${record.CH4 !== null ? record.CH4.toFixed(3) : 'N/A'}</td>
            <td>${record.CO_MQ9 !== null ? record.CO_MQ9.toFixed(3) : 'N/A'}</td>
            <td>${record.CO2 !== null ? record.CO2.toFixed(3) : 'N/A'}</td>
            <td>${record.NH3 !== null ? record.NH3.toFixed(3) : 'N/A'}</td>
            <td>${record.NOx !== null ? record.NOx.toFixed(3) : 'N/A'}</td>
            <td>${record.Alcohol !== null ? record.Alcohol.toFixed(3) : 'N/A'}</td>
            <td>${record.Benzene !== null ? record.Benzene.toFixed(3) : 'N/A'}</td>
            <td>${record.H2 !== null ? record.H2.toFixed(3) : 'N/A'}</td>
            <td>${record.Air !== null ? record.Air.toFixed(3) : 'N/A'}</td>
        `;
        row.addEventListener('click', () => showDetails(record));
        tableBody.appendChild(row);
    });
}

function renderMqPaginationControls(data) {
    const paginationControls = document.getElementById('mq-pagination-controls');
    const totalPages = Math.ceil(data.length / mqRecordsPerPage);

    if (!document.getElementById('mq-prev-button')) {
        const prevButton = document.createElement('button');
        prevButton.id = 'mq-prev-button';
        prevButton.innerText = 'Previous';
        paginationControls.appendChild(prevButton);
    }

    if (!document.getElementById('mq-next-button')) {
        const nextButton = document.createElement('button');
        nextButton.id = 'mq-next-button';
        nextButton.innerText = 'Next';
        paginationControls.appendChild(nextButton);
    }

    // Check if the dropdown already exists
    let pageSelect = document.getElementById('mq-page-select');
    if (!pageSelect) {
        // Create "Previous" button if it doesn't exist
        if (!document.getElementById('mq-prev-button')) {
            const prevButton = document.createElement('button');
            prevButton.id = 'mq-prev-button';
            prevButton.innerText = 'Previous';
            prevButton.classList.add('btn', 'btn-primary', 'me-2');
            prevButton.addEventListener('click', () => {
                if (mqCurrentPage > 1) {
                    mqCurrentPage--;
                    renderMqTablePage(data, mqCurrentPage);
                }
            });
            paginationControls.appendChild(prevButton);
        }

        // Create the dropdown
        pageSelect = document.createElement('select');
        pageSelect.id = 'mq-page-select';
        pageSelect.classList.add('form-select', 'd-inline-block', 'w-auto', 'me-2');
        pageSelect.addEventListener('change', (event) => {
            mqCurrentPage = parseInt(event.target.value, 10);
            renderMqTablePage(data, mqCurrentPage);
        });
        paginationControls.appendChild(pageSelect);

        // Create "Next" button if it doesn't exist
        if (!document.getElementById('mq-next-button')) {
            const nextButton = document.createElement('button');
            nextButton.id = 'mq-next-button';
            nextButton.innerText = 'Next';
            nextButton.classList.add('btn', 'btn-primary');
            nextButton.addEventListener('click', () => {
                if (mqCurrentPage < totalPages) {
                    mqCurrentPage++;
                    renderMqTablePage(data, mqCurrentPage);
                }
            });
            paginationControls.appendChild(nextButton);
        }
    }

    // Update the dropdown options if the total pages have changed
    if (pageSelect.options.length !== totalPages) {
        pageSelect.innerHTML = ''; // Clear existing options
        for (let i = 1; i <= totalPages; i++) {
            const option = document.createElement('option');
            option.value = i;
            option.text = `Page ${i}`;
            if (i === mqCurrentPage) {
                option.selected = true;
            }
            pageSelect.appendChild(option);
        }
    } else {
        // Ensure the current page is selected
        pageSelect.value = mqCurrentPage;
    }
}

function showDetails(record) {
    const modal = new bootstrap.Modal(document.getElementById('detailsModal'));

    // Populate modal details
    document.getElementById('modal-timestamp').innerText = new Date(record.timestamp).toLocaleString();
    document.getElementById('modal-temperature').innerText = record.temperature !== null ? record.temperature.toFixed(3) : 'N/A';
    document.getElementById('modal-humidity').innerText = record.humidity !== null ? record.humidity.toFixed(3) : 'N/A';
    document.getElementById('modal-lpg').innerText = record.LPG !== null ? record.LPG.toFixed(3) : 'N/A';
    document.getElementById('modal-co').innerText = record.CO !== null ? record.CO.toFixed(3) : 'N/A';
    document.getElementById('modal-smoke').innerText = record.Smoke !== null ? record.Smoke.toFixed(3) : 'N/A';
    document.getElementById('modal-co-mq7').innerText = record.CO_MQ7 !== null ? record.CO_MQ7.toFixed(3) : 'N/A';
    document.getElementById('modal-ch4').innerText = record.CH4 !== null ? record.CH4.toFixed(3) : 'N/A';
    document.getElementById('modal-co-mq9').innerText = record.CO_MQ9 !== null ? record.CO_MQ9.toFixed(3) : 'N/A';
    document.getElementById('modal-co2').innerText = record.CO2 !== null ? record.CO2.toFixed(3) : 'N/A';
    document.getElementById('modal-nh3').innerText = record.NH3 !== null ? record.NH3.toFixed(3) : 'N/A';
    document.getElementById('modal-nox').innerText = record.NOx !== null ? record.NOx.toFixed(3) : 'N/A';
    document.getElementById('modal-alcohol').innerText = record.Alcohol !== null ? record.Alcohol.toFixed(3) : 'N/A';
    document.getElementById('modal-benzene').innerText = record.Benzene !== null ? record.Benzene.toFixed(3) : 'N/A';
    document.getElementById('modal-h2').innerText = record.H2 !== null ? record.H2.toFixed(3) : 'N/A';
    document.getElementById('modal-air').innerText = record.Air !== null ? record.Air.toFixed(3) : 'N/A';

    // Show the modal
    modal.show();
}


setInterval(fetchMqData, 1000);
fetchMqData();
