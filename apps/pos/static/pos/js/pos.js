/* POS Alpine.js Logic, Quick Tender Buttons & Receipt Dialog */

function showToast(message, type = 'success') {
  let container = document.getElementById('posToastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'posToastContainer';
    container.className = 'position-fixed bottom-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
  }

  const bgClass = type === 'success' ? 'bg-success text-white' : (type === 'danger' ? 'bg-danger text-white' : 'bg-primary text-white');
  const icon = type === 'success' ? 'bi-check-circle-fill' : 'bi-exclamation-triangle-fill';

  const toastEl = document.createElement('div');
  toastEl.className = `toast align-items-center ${bgClass} border-0 show shadow-lg mb-2`;
  toastEl.role = 'alert';
  toastEl.innerHTML = `
    <div class="d-flex">
      <div class="toast-body fw-bold px-3 py-2">
        <i class="bi ${icon} me-2"></i>${message}
      </div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" onclick="this.closest('.toast').remove()"></button>
    </div>
  `;

  container.appendChild(toastEl);
  setTimeout(() => {
    if (toastEl && toastEl.parentNode) {
      toastEl.remove();
    }
  }, 4000);
}

function posCart() {
  return {
    searchQuery: '',
    categoryId: '',
    cart: [],
    paymentMethod: 'cash',
    amountPaid: 0,
    loading: false,

    // Employee Autocomplete Search State
    searchEmpQuery: '',
    showEmpDropdown: false,
    pnoInput: '',
    employee: null,
    searchingEmp: false,
    empError: '',
    allEmployees: [],

    // Receipt Modal State
    showReceipt: false,
    lastReceipt: null,

    init() {
      const el = document.getElementById('pos-employees-data');
      if (el) {
        try {
          this.allEmployees = JSON.parse(el.textContent);
        } catch(e) {}
      }

      // Hotkey listeners for cashier speed
      window.addEventListener('keydown', (e) => {
        if (e.key === 'F2') {
          e.preventDefault();
          const input = document.getElementById('posPnoInput');
          if (input) input.focus();
        } else if (e.key === 'Escape') {
          this.showEmpDropdown = false;
          if (this.showReceipt) {
            this.showReceipt = false;
          } else if (this.cart.length > 0) {
            if (confirm('Clear current order cart?')) this.clearCart();
          }
        }
      });
    },

    get filteredEmployees() {
      if (!this.searchEmpQuery.trim()) return this.allEmployees;
      const q = this.searchEmpQuery.toLowerCase().trim();
      return this.allEmployees.filter(emp =>
        emp.full_name.toLowerCase().includes(q) ||
        emp.pno.toLowerCase().includes(q) ||
        emp.department.toLowerCase().includes(q)
      );
    },

    selectEmp(emp) {
      this.employee = emp;
      this.searchEmpQuery = '';
      this.showEmpDropdown = false;
      this.empError = '';
    },

    setCategory(id) {
      this.categoryId = id;
      this.filterItems();
    },

    async filterItems() {
      try {
        const url = `/pos/search/?q=${encodeURIComponent(this.searchQuery)}&category=${encodeURIComponent(this.categoryId)}`;
        const res = await fetch(url);
        const data = await res.json();
        if (data.html) {
          const grid = document.getElementById('posItemGrid');
          if (grid) grid.innerHTML = data.html;
        }
      } catch (err) {
        console.error('Failed to filter items:', err);
      }
    },

    async lookupEmployee() {
      if (!this.searchEmpQuery.trim() && !this.pnoInput.trim()) {
        this.empError = 'Please enter name or P-Number.';
        return;
      }

      const q = this.searchEmpQuery.trim() || this.pnoInput.trim();
      this.searchingEmp = true;
      this.empError = '';

      try {
        const response = await fetch(`/pos/employee-lookup/?pno=${encodeURIComponent(q)}`);
        const data = await response.json();

        if (data.found) {
          this.employee = data;
          this.searchEmpQuery = '';
          this.pnoInput = '';
          this.showEmpDropdown = false;
          this.empError = '';
        } else {
          this.employee = null;
          this.empError = data.error || 'Employee not found.';
          showToast(this.empError, 'danger');
        }
      } catch (err) {
        this.empError = 'Failed to connect to employee registry.';
        showToast(this.empError, 'danger');
      } finally {
        this.searchingEmp = false;
      }
    },

    clearEmployee() {
      this.employee = null;
      this.searchEmpQuery = '';
      this.pnoInput = '';
      this.showEmpDropdown = false;
      this.empError = '';
    },

    addItemFromEl(el) {
      const id = parseInt(el.getAttribute('data-id'));
      const name = el.getAttribute('data-name');
      const price = parseFloat(el.getAttribute('data-price'));
      this.addItem({ id, name, price });
    },

    addItem(item) {
      const existing = this.cart.find(i => i.id === item.id);
      if (existing) {
        existing.qty++;
      } else {
        this.cart.push({ id: item.id, name: item.name, price: parseFloat(item.price), qty: 1 });
      }
    },

    updateQty(index, delta) {
      this.cart[index].qty += delta;
      if (this.cart[index].qty <= 0) {
        this.cart.splice(index, 1);
      }
    },

    updateQtyDirect(index, val) {
      const parsed = parseInt(val, 10);
      if (isNaN(parsed) || parsed <= 0) {
        this.cart[index].qty = 1;
      } else {
        this.cart[index].qty = parsed;
      }
    },

    removeItem(index) {
      this.cart.splice(index, 1);
    },

    clearCart() {
      this.cart = [];
      this.amountPaid = 0;
      this.employee = null;
      this.searchEmpQuery = '';
      this.pnoInput = '';
      this.showEmpDropdown = false;
      this.empError = '';
    },

    setTender(val) {
      if (val === 'exact') {
        this.amountPaid = this.total;
      } else {
        this.amountPaid = parseFloat(val);
      }
    },

    get total() {
      return this.cart.reduce((sum, i) => sum + (i.price * i.qty), 0);
    },

    get change() {
      return (this.amountPaid || 0) - this.total;
    },

    get availableTenders() {
      const denoms = [50, 100, 500, 1000, 5000];
      const billTotal = this.total;
      if (billTotal <= 0) return denoms;
      const filtered = denoms.filter(d => d >= billTotal);
      return filtered.length > 0 ? filtered : [5000];
    },

    get isInsufficientPaid() {
      return (this.amountPaid > 0) && (this.amountPaid < this.total);
    },

    get isCheckoutDisabled() {
      if (this.loading || this.cart.length === 0) return true;
      if (this.isInsufficientPaid) return true;
      return false;
    },

    async submitSale() {
      if (this.cart.length === 0 || this.isCheckoutDisabled) return;
      this.loading = true;

      const itemsPayload = [...this.cart];
      const totalVal = this.total;
      const paidVal = this.amountPaid || totalVal;
      const buyerName = this.employee ? this.employee.full_name : 'Walk-in Cash Customer';

      try {
        const response = await fetch('/pos/submit/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken(),
          },
          body: JSON.stringify({
            items: this.cart,
            payment_method: 'cash',
            amount_paid: paidVal,
            buyer_id: this.employee ? this.employee.id : null,
          })
        });

        const data = await response.json();
        if (response.ok) {
          showToast(`Sale completed! Change: ${data.change.toFixed(2)}`, 'success');
          
          if (data.receipt_url) {
            window.open(data.receipt_url, '_blank');
          }

          this.clearCart();
        } else {
          showToast(data.error || 'Failed to submit sale.', 'danger');
        }
      } catch (err) {
        showToast('Network error occurred during checkout.', 'danger');
      } finally {
        this.loading = false;
      }
    },

    printSlip() {
      window.print();
    }
  };
}

function getCsrfToken() {
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? match[1] : '';
}