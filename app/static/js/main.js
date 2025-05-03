$(document).ready(function () {
    // Sidebar toggle
    $('#sidebarCollapse').on('click', function () {
        $('#sidebar').toggleClass('active');
    });

    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // File upload drag and drop
    const uploadArea = document.querySelector('.upload-area');
    if (uploadArea) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, highlight, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, unhighlight, false);
        });

        function highlight(e) {
            uploadArea.classList.add('dragover');
        }

        function unhighlight(e) {
            uploadArea.classList.remove('dragover');
        }

        uploadArea.addEventListener('drop', handleDrop, false);

        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            handleFiles(files);
        }

        function handleFiles(files) {
            const fileInput = document.getElementById('file');
            fileInput.files = files;
            updateFileInfo(files[0]);
        }

        function updateFileInfo(file) {
            const fileInfo = document.getElementById('file-info');
            if (fileInfo) {
                fileInfo.textContent = `Selected file: ${file.name}`;
            }
        }
    }

    // Auto-hide alerts
    setTimeout(function() {
        $('.alert').fadeOut('slow');
    }, 5000);
});

// เพิ่มใน app/static/js/main.js
$(document).ready(function () {
    // ... existing code ...

    // Remember submenu state
    if (localStorage.getItem('settingsSubmenuOpen') === 'true') {
        $('#settingsSubmenu').addClass('show');
        $('#settingsSubmenu').parent().find('a').attr('aria-expanded', 'true');
    }

    // Save submenu state
    $('#settingsSubmenu').on('show.bs.collapse', function () {
        localStorage.setItem('settingsSubmenuOpen', 'true');
    });

    $('#settingsSubmenu').on('hide.bs.collapse', function () {
        localStorage.setItem('settingsSubmenuOpen', 'false');
    });

    // Auto expand if current page is in settings
    if (window.location.href.indexOf('/settings/') > -1) {
        $('#settingsSubmenu').addClass('show');
        $('#settingsSubmenu').parent().find('a').attr('aria-expanded', 'true');
    }
});