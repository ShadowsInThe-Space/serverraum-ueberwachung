/**
 * Charts-Manager für Serverraum-Überwachung
 * ========================================
 * Erstellt und verwaltet Chart.js Diagramme
 *
 * @author Marc-Dennis Haberland
 * @date 04.03.2026
 * Projekt: Serverraum-Überwachung (IHK-Abschlussprojekt)
 */

// Chart-Manager Objekt (verwendet bessere Praktiken)
const chartManager = {

    // Das Chart-Objekt
    verlaufChart: null,

    /**
     * Erstellt das Verlaufs-Diagramm
     * @param {array} messungen - Array von Messungen
     */
    erstelleVerlaufChart(messungen) {
        const canvas = document.getElementById('verlauf-chart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');

        // Daten vorbereiten
        const labels = messungen.map(m =>
            new Date(m.timestamp).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })
        );
        const werte = messungen.map(m => m.wert);

        // Altes Chart zerstören falls vorhanden
        if (this.verlaufChart) {
            this.verlaufChart.destroy();
        }

        // Neues Chart erstellen
        this.verlaufChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Wert',
                    data: werte,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 2,
                    pointHoverRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#9ca3af'
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#9ca3af'
                        },
                        beginAtZero: true
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });
    },

    /**
     * Zerstört alle Charts (beim Verlassen der Seite)
     */
    destroy() {
        if (this.verlaufChart) {
            this.verlaufChart.destroy();
            this.verlaufChart = null;
        }
    }
};

// Exportiere für globale Nutzung
window.chartManager = chartManager;

// Kompatibilitätsfunktion für dashboard.js
window.aktualisiereVerlaufChart = function(messungen, sensorId) {
    chartManager.erstelleVerlaufChart(messungen);
};
