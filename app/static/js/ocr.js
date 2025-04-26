/**
 * JavaScript สำหรับจัดการการอัพโหลดใบเสร็จและ OCR
 */

document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const ocrUploadBtn = document.getElementById('ocr-upload-btn');
    const receiptInput = document.getElementById('receipt');
    const receiptPreview = document.getElementById('receipt-preview');
    const ocrLoadingIndicator = document.getElementById('ocr-loading');
    const ocrResultsContainer = document.getElementById('ocr-results');

    // Form fields to be filled with OCR data
    const amountInput = document.getElementById('amount');
    const dateInput = document.getElementById('transaction_date');
    const descriptionInput = document.getElementById('description');

    // Only initialize if OCR elements exist
    if (ocrUploadBtn && receiptInput) {
        // Handle OCR upload button click
        ocrUploadBtn.addEventListener('click', function(e) {
            e.preventDefault();
            receiptInput.click();
        });

        // Handle receipt file selection
        receiptInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                // Show loading indicator
                if (ocrLoadingIndicator) {
                    ocrLoadingIndicator.style.display = 'block';
                }

                // Clear previous results
                if (ocrResultsContainer) {
                    ocrResultsContainer.innerHTML = '';
                    ocrResultsContainer.style.display = 'none';
                }

                // Show preview
                const reader = new FileReader();
                reader.onload = function(e) {
                    receiptPreview.src = e.target.result;
                    receiptPreview.style.display = 'block';
                };
                reader.readAsDataURL(this.files[0]);

                // Process OCR
                processOCR(this.files[0]);
            }
        });

        // Process OCR
        function processOCR(file) {
            const formData = new FormData();
            formData.append('receipt', file);

            fetch('/api/ocr/receipt', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                // Hide loading indicator
                if (ocrLoadingIndicator) {
                    ocrLoadingIndicator.style.display = 'none';
                }

                if (data.success) {
                    // Fill form fields with extracted data
                    if (data.data.total_amount && amountInput) {
                        amountInput.value = data.data.total_amount;
                    }

                    if (data.data.date && dateInput) {
                        dateInput.value = data.data.date;
                    }

                    if (data.data.vendor && descriptionInput) {
                        descriptionInput.value = data.data.vendor;
                    }

                    // Show OCR results
                    if (ocrResultsContainer) {
                        ocrResultsContainer.innerHTML = `
                            <div class="alert alert-success">
                                <h5>ข้อมูลที่ดึงได้:</h5>
                                <ul>
                                    <li><strong>วันที่:</strong> ${data.data.date || 'ไม่พบ'}</li>
                                    <li><strong>จำนวนเงิน:</strong> ${data.data.total_amount ? data.data.total_amount.toLocaleString('th-TH', {style: 'currency', currency: 'THB'}) : 'ไม่พบ'}</li>
                                    <li><strong>ร้านค้า:</strong> ${data.data.vendor || 'ไม่พบ'}</li>
                                </ul>
                            </div>
                        `;
                        ocrResultsContainer.style.display = 'block';
                    }
                } else {
                    // Show error
                    if (ocrResultsContainer) {
                        ocrResultsContainer.innerHTML = `
                            <div class="alert alert-danger">
                                <p><strong>เกิดข้อผิดพลาด:</strong> ${data.error}</p>
                                <p>กรุณากรอกข้อมูลด้วยตนเอง</p>
                            </div>
                        `;
                        ocrResultsContainer.style.display = 'block';
                    }
                }
            })
            .catch(error => {
                console.error('Error during OCR processing:', error);

                // Hide loading indicator
                if (ocrLoadingIndicator) {
                    ocrLoadingIndicator.style.display = 'none';
                }

                // Show error
                if (ocrResultsContainer) {
                    ocrResultsContainer.innerHTML = `
                        <div class="alert alert-danger">
                            <p><strong>เกิดข้อผิดพลาด:</strong> ไม่สามารถประมวลผลใบเสร็จได้</p>
                            <p>กรุณากรอกข้อมูลด้วยตนเอง</p>
                        </div>
                    `;
                    ocrResultsContainer.style.display = 'block';
                }
            });
        }
    }
});