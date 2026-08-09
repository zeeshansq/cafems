/**
 * Daily Menu Entry & Costing Form JS
 * Handles AJAX live recalculation, dish select dropdown sync, spinner animations, and auto-syncing.
 */
document.addEventListener('DOMContentLoaded', function() {
  const btnRecalculate = document.getElementById('btnRecalculate');
  const spinner = document.getElementById('spinnerRecalc');

  // Dish select sync
  const dishSelectEl = document.getElementById('id_dish_select');
  const dishNameEl = document.getElementById('id_dish_name');
  if (dishSelectEl && dishNameEl) {
    dishSelectEl.addEventListener('change', function() {
      if (this.value) {
        dishNameEl.value = this.value;
      }
    });
  }

  function triggerRecalculate() {
    if (spinner) {
      spinner.classList.add('spin-animation');
    }

    const csrfEl = document.querySelector('[name=csrfmiddlewaretoken]');
    const dateEl = document.getElementById('id_est_date');
    const rotiPriceObjEl = document.getElementById('id_roti_price_obj');
    const rotiEl = document.getElementById('id_roti_type');
    const sweetEl = document.getElementById('id_sweet');
    const totalExpEl = document.getElementById('id_total_expense');
    const adjEl = document.getElementById('id_adjustment_amount');

    if (!csrfEl || !dateEl) return;

    const formData = new FormData();
    formData.append('csrfmiddlewaretoken', csrfEl.value);
    formData.append('date', dateEl.value);
    formData.append('roti_price_obj', rotiPriceObjEl ? rotiPriceObjEl.value : '');
    formData.append('roti_type', rotiEl ? rotiEl.value : '');
    formData.append('sweet', sweetEl ? sweetEl.value : '');
    formData.append('total_expense', totalExpEl ? totalExpEl.value : '0');
    formData.append('adjustment_amount', adjEl ? adjEl.value : '0');

    fetch(recalculateUrl, {
      method: 'POST',
      body: formData
    })
    .then(response => response.json())
    .then(data => {
      if (spinner) {
        spinner.classList.remove('spin-animation');
      }
      if (data.status === 'success') {
        const actualTokensEl = document.getElementById('id_actual_tokens_issued');
        const actualRotiEl = document.getElementById('id_actual_extra_roti_issued');
        const actualSweetEl = document.getElementById('id_actual_extra_sweet_issued');
        const rotiPriceEl = document.getElementById('id_roti_unit_price');
        const sweetPriceEl = document.getElementById('id_sweet_unit_price');
        const tokenExpEl = document.getElementById('id_token_expense');
        const pricePerTokenEl = document.getElementById('id_price_per_token');

        if (actualTokensEl) actualTokensEl.value = data.actual_tokens_issued;
        if (actualRotiEl) actualRotiEl.value = data.actual_extra_roti_issued;
        if (actualSweetEl) actualSweetEl.value = data.actual_extra_sweet_issued;
        if (rotiPriceEl) rotiPriceEl.value = data.roti_unit_price;
        if (sweetPriceEl) sweetPriceEl.value = data.sweet_unit_price;
        if (tokenExpEl) tokenExpEl.value = data.token_expense;
        if (pricePerTokenEl) pricePerTokenEl.value = data.price_per_token;

        const lblRoti = document.getElementById('lblRotiUnitPrice');
        const lblSweet = document.getElementById('lblSweetUnitPrice');
        if (lblRoti) lblRoti.textContent = data.roti_unit_price;
        if (lblSweet) lblSweet.textContent = data.sweet_unit_price;
      }
    })
    .catch(err => {
      if (spinner) {
        spinner.classList.remove('spin-animation');
      }
      console.error('Recalculate error:', err);
    });
  }

  if (btnRecalculate) {
    btnRecalculate.addEventListener('click', triggerRecalculate);
  }

  ['id_total_expense', 'id_adjustment_amount', 'id_roti_price_obj', 'id_roti_type', 'id_sweet', 'id_est_date'].forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener('change', triggerRecalculate);
    }
  });
});
