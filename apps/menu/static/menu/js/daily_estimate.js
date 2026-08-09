/**
 * Daily Menu Entries List JS
 * Handles date range filters, pagination actions, and report triggers.
 */
document.addEventListener('DOMContentLoaded', function() {
  console.log('Daily Entries List JS initialized.');

  const printReportBtn = document.getElementById('btnPrintRangeReport');
  if (printReportBtn) {
    printReportBtn.addEventListener('click', function(e) {
      const url = this.getAttribute('data-url');
      if (url) {
        window.open(url, '_blank');
      }
    });
  }
});
