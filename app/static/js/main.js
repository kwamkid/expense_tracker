/* app/static/js/main.js */

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

    // Icon selector for categories
    const iconInput = document.getElementById('icon');
    const iconPreview = document.getElementById('icon-preview');
    const iconSelector = document.getElementById('icon-selector');

    if (iconInput && iconPreview) {
        // Update preview when icon changes
        iconInput.addEventListener('input', function() {
            iconPreview.className = `fas fa-${this.value} fa-lg`;
        });

        // Initial icon preview
        if (iconInput.value) {
            iconPreview.className = `fas fa-${iconInput.value} fa-lg`;
        }

        // Icon selector
        if (iconSelector) {
            // Common Font Awesome icons
            const commonIcons = [
                'money-bill', 'coins', 'credit-card', 'wallet', 'piggy-bank',
                'shopping-cart', 'store', 'utensils', 'coffee', 'wine-glass',
                'tshirt', 'shoe-prints', 'socks', 'hat-cowboy', 'glasses',
                'home', 'building', 'city', 'hotel', 'house',
                'car', 'bus', 'train', 'plane', 'ship',
                'graduation-cap', 'book', 'pen', 'pencil-alt', 'paint-brush',
                'heartbeat', 'medkit', 'hospital', 'pills', 'thermometer',
                'gamepad', 'film', 'music', 'headphones', 'ticket-alt',
                'dumbbell', 'running', 'hiking', 'swimming-pool', 'bicycle',
                'baby', 'child', 'dog', 'cat', 'bone',
                'gift', 'gem', 'crown', 'award', 'trophy',
                'tools', 'wrench', 'screwdriver', 'hammer', 'toolbox',
                'mobile-alt', 'laptop', 'desktop', 'tv', 'camera',
                'plane-departure', 'plane-arrival', 'map-marker-alt', 'globe', 'passport',
                'birthday-cake', 'glass-cheers', 'beer', 'wine-bottle', 'cocktail',
                'pizza-slice', 'hamburger', 'ice-cream', 'candy-cane', 'cookie',
                'tags', 'tag', 'percentage', 'donate', 'hand-holding-usd',
                'chart-line', 'chart-bar', 'chart-pie', 'chart-area', 'calculator'
            ];

            // Generate icon options
            let iconsHtml = '';
            commonIcons.forEach(icon => {
                iconsHtml += `<div class="icon-option" data-icon="${icon}"><i class="fas fa-${icon}"></i></div>`;
            });
            iconSelector.innerHTML = iconsHtml;

            // Mark the selected icon
            if (iconInput.value) {
                const selectedOption = iconSelector.querySelector(`[data-icon="${iconInput.value}"]`);
                if (selectedOption) {
                    selectedOption.classList.add('selected');
                }
            }

            // Handle icon selection
            const iconOptions = iconSelector.querySelectorAll('.icon-option');
            iconOptions.forEach(option => {
                option.addEventListener('click', function() {
                    const icon = this.getAttribute('data-icon');

                    // Update input value
                    iconInput.value = icon;

                    // Update preview
                    iconPreview.className = `fas fa-${icon} fa-lg`;

                    // Update selected class
                    iconOptions.forEach(opt => opt.classList.remove('selected'));
                    this.classList.add('selected');
                });
            });
        }
    }

    // Date range picker for transaction reports
    const dateRangeInput = document.getElementById('date-range');
    if (dateRangeInput) {
        const startDateInput = document.getElementById('start_date');
        const endDateInput = document.getElementById('end_date');

        // Initialize date range picker
        $(dateRangeInput).daterangepicker({
            opens: 'left',
            autoApply: true,
            ranges: {
                'วันนี้': [moment(), moment()],
                'เมื่อวาน': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
                '7 วันที่ผ่านมา': [moment().subtract(6, 'days'), moment()],
                '30 วันที่ผ่านมา': [moment().subtract(29, 'days'), moment()],
                'เดือนนี้': [moment().startOf('month'), moment().endOf('month')],
                'เดือนที่แล้ว': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')]
            },
            locale: {
                format: 'DD/MM/YYYY',
                applyLabel: 'ตกลง',
                cancelLabel: 'ยกเลิก',
                customRangeLabel: 'กำหนดเอง',
                daysOfWeek: ['อา', 'จ', 'อ', 'พ', 'พฤ', 'ศ', 'ส'],
                monthNames: [
                    'มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน', 'พฤษภาคม', 'มิถุนายน',
                    'กรกฎาคม', 'สิงหาคม', 'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม'
                ]
            }
        }, function(start, end) {
            // Update hidden inputs with selected dates
            startDateInput.value = start.format('YYYY-MM-DD');
            endDateInput.value = end.format('YYYY-MM-DD');
        });
    }

    // Export report buttons
    const exportButtons = document.querySelectorAll('.export-report-btn');
    exportButtons.forEach(button => {
        button.addEventListener('click', function() {
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

    // Print report button
    const printButton = document.getElementById('print-report-btn');
    if (printButton) {
        printButton.addEventListener('click', function() {
            window.print();
        });
    }

    // Transaction filters
    const filterForm = document.getElementById('filter-form');
    if (filterForm) {
        // Auto-submit form when select filters change
        const selectFilters = filterForm.querySelectorAll('select');
        selectFilters.forEach(select => {
            select.addEventListener('change', function() {
                filterForm.submit();
            });
        });
    }

    // Confirm delete modals
    const deleteButtons = document.querySelectorAll('[data-bs-toggle="delete-confirm"]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();

            const id = this.getAttribute('data-id');
            const type = this.getAttribute('data-type');
            const name = this.getAttribute('data-name');

            // Set modal content
            const modalTitle = document.getElementById('deleteModalLabel');
            const modalBody = document.getElementById('deleteModalBody');
            const deleteForm = document.getElementById('deleteForm');

            modalTitle.textContent = `ยืนยันการลบ${type}`;
            modalBody.textContent = `คุณต้องการลบ${type} "${name}" ใช่หรือไม่?`;
            deleteForm.action = this.getAttribute('href');

            // Show modal
            const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
            modal.show();
        });
    });

    // Receipt modal for viewing images
    const viewReceiptLinks = document.querySelectorAll('.view-receipt');
    if (viewReceiptLinks.length > 0) {
        const receiptModal = document.getElementById('receiptModal');
        const receiptModalImage = document.getElementById('receiptModalImage');

        viewReceiptLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();

                // Set image source in modal
                receiptModalImage.src = this.getAttribute('data-img-url');

                // Show modal
                const modal = new bootstrap.Modal(receiptModal);
                modal.show();
            });
        });
    }

    // Year/month selector in reports
    const yearSelect = document.getElementById('year');
    const monthSelect = document.getElementById('month');

    if (yearSelect && monthSelect) {
        // Auto-submit form when year/month changes
        yearSelect.addEventListener('change', function() {
            document.getElementById('report-form').submit();
        });

        monthSelect.addEventListener('change', function() {
            document.getElementById('report-form').submit();
        });
    }
});