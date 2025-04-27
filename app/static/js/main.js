/* app/static/js/main.js - ปรับปรุงประสิทธิภาพ */

/**
 * Debounce function - ลดจำนวนครั้งที่ฟังก์ชันจะถูกเรียกในช่วงเวลาสั้นๆ
 * @param {Function} func - ฟังก์ชันที่ต้องการ debounce
 * @param {number} wait - ระยะเวลารอ (ms)
 * @returns {Function} - ฟังก์ชันที่ผ่านการ debounce
 */
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

/**
 * ฟังก์ชันสำหรับจัดการการอัพเดทสถานะธุรกรรม
 * ปรับปรุงให้มีการตรวจสอบและประมวลผลที่ถูกต้อง
 */
function initTransactionStatusToggles() {
  // DOM elements
  const statusToggles = document.querySelectorAll('.status-toggle');

  if (statusToggles.length === 0) return;

  // เก็บสถานะปัจจุบันของแต่ละรายการ
  const currentStates = new Map();

  // บันทึกสถานะเริ่มต้น
  statusToggles.forEach(toggle => {
    const transactionId = toggle.getAttribute('data-transaction-id');
    currentStates.set(transactionId, toggle.checked);
  });

  // ตั้งค่า event listeners
  statusToggles.forEach(toggle => {
    toggle.addEventListener('change', function(e) {
      // ป้องกันการทำงานของ event listener ดั้งเดิม
      e.preventDefault();

      const transactionId = this.getAttribute('data-transaction-id');
      const transactionType = this.getAttribute('data-transaction-type');
      const newStatus = this.checked ? 'completed' : 'pending';
      const row = this.closest('tr');

      // เปลี่ยนกลับเป็นสถานะเดิมก่อนเพื่อรอผลการอัพเดท
      this.checked = currentStates.get(transactionId);

      // แสดงการยืนยันก่อนเปลี่ยนสถานะ
      const confirmMessage = this.checked
        ? 'คุณต้องการเปลี่ยนสถานะเป็น "รอดำเนินการ" ใช่หรือไม่?\nการเปลี่ยนแปลงนี้จะมีผลต่อยอดเงินในบัญชี'
        : 'คุณต้องการเปลี่ยนสถานะเป็น "เสร็จสิ้น" ใช่หรือไม่?\nการเปลี่ยนแปลงนี้จะมีผลต่อยอดเงินในบัญชี';

      if (confirm(confirmMessage)) {
        // แสดง loading
        row.style.opacity = '0.5';

        // ปิดการใช้งานชั่วคราว
        toggle.disabled = true;

        // ส่งคำขอ AJAX เพื่ออัพเดตสถานะ
        fetch('/api/transactions/update-status', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
          },
          body: JSON.stringify({
            id: transactionId,
            status: newStatus
          })
        })
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          row.style.opacity = '1';
          toggle.disabled = false;

          if (data.success) {
            // อัพเดทสถานะการทำงานปัจจุบัน
            this.checked = newStatus === 'completed';
            currentStates.set(transactionId, this.checked);

            // อัพเดทข้อมูลที่แสดงในตาราง (ถ้ามี)
            const statusLabel = row.querySelector('.status-label');
            if (statusLabel) {
              statusLabel.textContent = newStatus;
            }

            // แสดงข้อความแจ้งเตือน
            const alertHTML = `
              <div class="alert alert-success alert-dismissible fade show">
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                <i class="fas fa-check-circle me-2"></i>อัพเดตสถานะธุรกรรมเรียบร้อยแล้ว (${data.account ? data.account.name + ': ' + data.account.balance.toLocaleString('th-TH', {minimumFractionDigits: 2}) + ' ฿' : ''})
              </div>
            `;
            document.querySelector('.container-fluid').insertAdjacentHTML('afterbegin', alertHTML);

            // เลื่อนไปด้านบนเพื่อให้เห็นข้อความแจ้งเตือน
            window.scrollTo({ top: 0, behavior: 'smooth' });

            // ซ่อนข้อความแจ้งเตือนอัตโนมัติหลังจาก 5 วินาที
            setTimeout(function() {
              const alertElement = document.querySelector('.alert-success');
              if (alertElement) {
                const bsAlert = new bootstrap.Alert(alertElement);
                bsAlert.close();
              }
            }, 5000);
          } else {
            // แสดงข้อความแจ้งเตือนข้อผิดพลาด
            const alertHTML = `
              <div class="alert alert-danger alert-dismissible fade show">
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                <i class="fas fa-exclamation-circle me-2"></i>เกิดข้อผิดพลาด: ${data.error}
              </div>
            `;
            document.querySelector('.container-fluid').insertAdjacentHTML('afterbegin', alertHTML);

            // เลื่อนไปด้านบนเพื่อให้เห็นข้อความแจ้งเตือน
            window.scrollTo({ top: 0, behavior: 'smooth' });
          }
        })
        .catch(error => {
          console.error('Error:', error);
          row.style.opacity = '1';
          toggle.disabled = false;

          // แสดงข้อความแจ้งเตือนข้อผิดพลาด
          const alertHTML = `
            <div class="alert alert-danger alert-dismissible fade show">
              <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
              <i class="fas fa-exclamation-circle me-2"></i>เกิดข้อผิดพลาดในการสื่อสารกับเซิร์ฟเวอร์
            </div>
          `;
          document.querySelector('.container-fluid').insertAdjacentHTML('afterbegin', alertHTML);

          // เลื่อนไปด้านบนเพื่อให้เห็นข้อความแจ้งเตือน
          window.scrollTo({ top: 0, behavior: 'smooth' });
        });
      }
    });
  });
}

// DOM Ready handler - รวมการทำงานทั้งหมดไว้ในฟังก์ชันเดียว
document.addEventListener('DOMContentLoaded', function() {
  // Initialize tooltips
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // Initialize popovers
  const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
  popoverTriggerList.map(function (popoverTriggerEl) {
      return new bootstrap.Popover(popoverTriggerEl);
  });

  // Auto-hide flash messages after 5 seconds
  setTimeout(function() {
      const alerts = document.querySelectorAll('.alert:not(.alert-important)');
      alerts.forEach(function(alert) {
          const bsAlert = new bootstrap.Alert(alert);
          bsAlert.close();
      });
  }, 5000);

  // DOM Elements
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');
  const mainContent = document.getElementById('mainContent');
  const mobileMenuToggle = document.getElementById('mobileMenuToggle');
  const mobileUserMenuToggle = document.getElementById('mobileUserMenuToggle');
  const mobileUserDropdown = document.getElementById('mobileUserDropdown');
  const menuBackdrop = document.getElementById('menuBackdrop');

  // Initialize variables
  let isMobile = window.innerWidth <= 768;
  let sidebarVisible = false;
  let userDropdownVisible = false;

  // เริ่มต้นค่าที่เหมาะสมตามขนาดหน้าจอ
  function initializeLayoutState() {
    isMobile = window.innerWidth <= 768;

    // ตั้งค่าสถานะเริ่มต้น
    if (isMobile) {
      if (sidebar) sidebar.classList.remove('show');
      if (menuBackdrop) menuBackdrop.style.display = 'none';
      document.body.style.overflow = '';
    }

    // ซ่อน dropdown
    if (mobileUserDropdown) {
      mobileUserDropdown.classList.remove('show');
    }
  }

  // เรียกฟังก์ชันเริ่มต้น
  initializeLayoutState();

  // Toggle sidebar on larger screens
  if (sidebarToggle && sidebar && mainContent) {
    sidebarToggle.addEventListener('click', function() {
      if (!isMobile) {
        sidebar.classList.toggle('collapsed');
        mainContent.classList.toggle('sidebar-collapsed');
      }
    });
  }

  // Toggle mobile sidebar with improved performance
  if (mobileMenuToggle && sidebar && menuBackdrop) {
    mobileMenuToggle.addEventListener('click', function() {
      sidebarVisible = !sidebarVisible;

      // เพิ่ม/ลบ class แค่ครั้งเดียว
      if (sidebarVisible) {
        sidebar.classList.add('show');
        menuBackdrop.style.display = 'block';
        menuBackdrop.classList.add('show');
        document.body.style.overflow = 'hidden';
      } else {
        sidebar.classList.remove('show');
        menuBackdrop.classList.remove('show');
        setTimeout(() => {
          if (!sidebarVisible) menuBackdrop.style.display = 'none';
        }, 200); // รอให้ transition จบ
        document.body.style.overflow = '';
      }
    });
  }

  // Toggle user dropdown - ปรับปรุงประสิทธิภาพ
  if (mobileUserMenuToggle && mobileUserDropdown) {
    mobileUserMenuToggle.addEventListener('click', function(e) {
      e.stopPropagation();
      userDropdownVisible = !userDropdownVisible;

      if (userDropdownVisible) {
        mobileUserDropdown.classList.add('show');
      } else {
        mobileUserDropdown.classList.remove('show');
      }
    });
  }

  // Close sidebar when clicking on backdrop - ปรับปรุงให้ทำงานอย่างมีประสิทธิภาพ
  if (menuBackdrop && sidebar) {
    menuBackdrop.addEventListener('click', function() {
      sidebarVisible = false;
      sidebar.classList.remove('show');
      menuBackdrop.classList.remove('show');
      setTimeout(() => {
        if (!sidebarVisible) menuBackdrop.style.display = 'none';
      }, 200); // รอให้ transition จบ
      document.body.style.overflow = '';
    });
  }

  // Close user dropdown when clicking outside - ปรับปรุงประสิทธิภาพ
  document.addEventListener('click', function(e) {
    if (mobileUserDropdown && userDropdownVisible &&
        mobileUserMenuToggle && !mobileUserMenuToggle.contains(e.target) &&
        !mobileUserDropdown.contains(e.target)) {
      userDropdownVisible = false;
      mobileUserDropdown.classList.remove('show');
    }
  });

  // Close sidebar when clicking on links - ใช้ event delegation เพื่อประสิทธิภาพ
  if (sidebar) {
    sidebar.addEventListener('click', function(e) {
      const target = e.target.closest('.nav-link');
      if (target && isMobile) {
        sidebarVisible = false;
        sidebar.classList.remove('show');
        if (menuBackdrop) {
          menuBackdrop.classList.remove('show');
          setTimeout(() => {
            if (!sidebarVisible) menuBackdrop.style.display = 'none';
          }, 200);
        }
        document.body.style.overflow = '';
      }
    });
  }

  // ใช้ debounce เพื่อลดการเรียกฟังก์ชันซ้ำๆ เมื่อ resize
  const handleResize = debounce(function() {
    const wasIsMobile = isMobile;
    isMobile = window.innerWidth <= 768;

    // เปลี่ยนโหมดเฉพาะเมื่อมีการเปลี่ยนจากมือถือเป็น desktop หรือกลับกัน
    if (wasIsMobile !== isMobile) {
      if (isMobile) {
        // เปลี่ยนจาก desktop เป็นมือถือ
        if (sidebar) sidebar.classList.remove('show');
        if (menuBackdrop) menuBackdrop.style.display = 'none';
        document.body.style.overflow = '';
      } else {
        // เปลี่ยนจากมือถือเป็น desktop
        if (menuBackdrop) menuBackdrop.style.display = 'none';
        document.body.style.overflow = '';
      }

      // รีเซ็ตสถานะ
      sidebarVisible = false;
      userDropdownVisible = false;

      if (mobileUserDropdown) {
        mobileUserDropdown.classList.remove('show');
      }
    }
  }, 150); // debounce 150ms

  // เพิ่ม event listener แค่ครั้งเดียว
  window.addEventListener('resize', handleResize);

  // Transaction form: Toggle category options based on transaction type
  const transactionTypeSelect = document.getElementById('type');
  const categorySelect = document.getElementById('category_id');

  if (transactionTypeSelect && categorySelect) {
      // Function to load categories via AJAX
      function loadCategories(type) {
          fetch(`/api/categories?type=${type}`)
              .then(response => response.json())
              .then(data => {
                  // Clear current options
                  categorySelect.innerHTML = '';

                  // Add new options
                  data.forEach(category => {
                      const option = document.createElement('option');
                      option.value = category.id;
                      option.textContent = category.name;
                      categorySelect.appendChild(option);
                  });
              })
              .catch(error => console.error('Error loading categories:', error));
      }

      // Load categories when type changes
      transactionTypeSelect.addEventListener('change', function() {
          loadCategories(this.value);
      });

      // Initial load
      if (transactionTypeSelect.value) {
          loadCategories(transactionTypeSelect.value);
      }
  }

  // Preview receipt image before upload
  const receiptInput = document.getElementById('receipt');
  const receiptPreview = document.getElementById('receipt-preview');

  if (receiptInput && receiptPreview) {
      receiptInput.addEventListener('change', function() {
          if (this.files && this.files[0]) {
              const reader = new FileReader();

              reader.onload = function(e) {
                  receiptPreview.src = e.target.result;
                  receiptPreview.style.display = 'block';
              }

              reader.readAsDataURL(this.files[0]);
          }
      });
  }

  // Receipt image modal
  const receiptThumbnails = document.querySelectorAll('.receipt-thumbnail');

  receiptThumbnails.forEach(function(thumbnail) {
      thumbnail.addEventListener('click', function() {
          const modal = new bootstrap.Modal(document.getElementById('receiptModal'));
          const modalImage = document.getElementById('receiptModalImage');

          modalImage.src = this.src;
          modal.show();
      });
  });

  // เรียกใช้ฟังก์ชันการจัดการสถานะธุรกรรม
  initTransactionStatusToggles();

  // ฟังก์ชันสำหรับฟอร์มอื่นๆ ที่มีในโค้ดเดิม
  // Color picker for categories
  const colorPicker = document.getElementById('color');
  const colorPreview = document.getElementById('color-preview');

  if (colorPicker && colorPreview) {
      // Update preview when color changes
      colorPicker.addEventListener('input', function() {
          colorPreview.style.backgroundColor = this.value;
      });

      // Initial color preview
      if (colorPicker.value) {
          colorPreview.style.backgroundColor = colorPicker.value;
      }
  }

  // สำหรับหน้ารายงาน
  // Export report buttons
  const exportButtons = document.querySelectorAll('.export-report-btn');
  if (exportButtons.length > 0) {
    exportButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const format = this.getAttribute('data-format');
            const reportType = this.getAttribute('data-report');
            const params = new URLSearchParams(window.location.search);

            // Build export URL with current filters
            let exportUrl = `/reports/export/${reportType}?format=${format}`;

            // Add other parameters from the current page
            params.forEach((value, key) => {
                if (key !== 'page') {
                    exportUrl += `&${key}=${value}`;
                }
            });

            // Navigate to export URL
            window.location.href = exportUrl;
        });
    });
  }

  // Print report button
  const printButton = document.getElementById('print-report-btn');
  if (printButton) {
    printButton.addEventListener('click', function(e) {
        e.preventDefault();
        window.print();
    });
  }
});