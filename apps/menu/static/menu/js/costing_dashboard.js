/**
 * Lunch Costing Dashboard JS
 * Handles interactive behaviors, live metrics refresh, and theme change events.
 */
document.addEventListener('DOMContentLoaded', function() {
  console.log('Lunch Costing Dashboard initialized.');

  // Initialize tooltips if bootstrap is available
  if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl);
    });
  }

  // React to dark/light theme switch
  const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
      if (mutation.attributeName === 'data-theme') {
        const newTheme = document.documentElement.getAttribute('data-theme');
        console.log('Dashboard theme switched to:', newTheme);
      }
    });
  });

  observer.observe(document.documentElement, { attributes: true });
});
