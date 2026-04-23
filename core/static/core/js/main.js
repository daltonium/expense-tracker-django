// Auto-dismiss alerts after 4 seconds
document.querySelectorAll('.alert').forEach(alert => {
    setTimeout(() => {
        alert.style.transition = 'opacity 0.4s';
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 400);
    }, 4000);
});

// Add tabular-nums to all money values
document.querySelectorAll('.kpi-value, td').forEach(el => {
    if (el.textContent.includes('₹')) {
        el.style.fontVariantNumeric = 'tabular-nums';
    }
});