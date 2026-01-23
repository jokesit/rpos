


document.addEventListener("DOMContentLoaded", function () {
    
    const getChartData = (id) => {
        const el = document.getElementById(id);
        try {
            return el ? JSON.parse(el.textContent) : [];
        } catch (e) {
            console.error(`Error parsing data for ${id}:`, e);
            return [];
        }
    };

    const chartDates = getChartData("data-chart-dates");
    const chartRevenues = getChartData("data-chart-revenues");
    const topItemLabels = getChartData("data-top-items-labels");
    const topItemData = getChartData("data-top-items-data");

    Chart.defaults.font.family = "'Prompt', sans-serif";
    Chart.defaults.color = '#64748b';

    // -------------------------------------------------
    // A. Sales Trend Chart
    // -------------------------------------------------
    const salesCtx = document.getElementById("salesChart");
    if (salesCtx && chartDates.length > 0) {
        new Chart(salesCtx.getContext("2d"), {
            type: "line",
            data: {
                labels: chartDates,
                datasets: [{
                    label: "ยอดขาย",
                    data: chartRevenues,
                    borderColor: "#2563eb",
                    backgroundColor: "rgba(37, 99, 235, 0.1)",
                    borderWidth: 2,
                    tension: 0.3, // ถ้ายังช้าอยู่ ให้แก้เป็น 0 (เส้นตรง)
                    fill: true,
                    pointRadius: 3, // ลดขนาดจุด
                    pointHoverRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false, // ⭐ สำคัญมาก: ป้องกันกราฟยืดจนสูงทะลุจอ
                animation: false, // ⭐ ปิด Animation เพื่อความลื่นไหล (หรือเอาออกถ้าอยากได้ Effect)
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (context) => '฿' + context.parsed.y.toLocaleString()
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { borderDash: [4, 4] },
                        ticks: { callback: (val) => '฿' + val.toLocaleString() }
                    },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    // -------------------------------------------------
    // B. Top Items Chart
    // -------------------------------------------------
    const itemsCtx = document.getElementById("topItemsChart");
    if (itemsCtx && topItemLabels.length > 0) {
        new Chart(itemsCtx.getContext("2d"), {
            type: "doughnut",
            data: {
                labels: topItemLabels,
                datasets: [{
                    data: topItemData,
                    backgroundColor: [
                        "#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6",
                        "#6366f1", "#ec4899", "#14b8a6", "#f97316", "#64748b"
                    ],
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false, // ⭐ สำคัญมาก
                animation: false, // ⭐ ปิด Animation
                plugins: {
                    legend: {
                        position: "right",
                        labels: { boxWidth: 12, usePointStyle: true, padding: 10 }
                    }
                }
            }
        });
    }
});