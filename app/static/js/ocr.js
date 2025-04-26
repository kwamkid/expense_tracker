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

                        // เพิ่มเลขที่ใบเสร็จถ้ามี
                        if (data.data.receipt_no) {
                            descriptionInput.value += ` (เลขที่: ${data.data.receipt_no})`;
                        }
                    }

                    // Show OCR results
                    if (ocrResultsContainer) {
                        // สร้างผลลัพธ์ที่แสดงได้ชัดเจนว่าข้อมูลไหนถูกดึงได้บ้าง
                        let resultHTML = '<div class="alert ';

                        // ถ้ามี warning แสดงว่าไม่พบข้อมูล
                        if (data.warning) {
                            resultHTML += 'alert-warning"><i class="fas fa-exclamation-triangle me-2"></i><strong>ไม่พบข้อมูล:</strong> ' + data.warning;
                        }
                        // ถ้ามีข้อมูลอย่างน้อย 1 อย่าง ถือว่าสำเร็จบางส่วน
                        else if (Object.values(data.data).some(val => val !== null)) {
                            resultHTML += 'alert-success"><i class="fas fa-check-circle me-2"></i><strong>ดึงข้อมูลสำเร็จ</strong>';
                        }
                        // ถ้าไม่มีข้อมูลใดเลย แต่ยังถือว่าสำเร็จในการประมวลผล
                        else {
                            resultHTML += 'alert-info"><i class="fas fa-info-circle me-2"></i><strong>ประมวลผลสำเร็จ</strong> แต่ไม่พบข้อมูลจากใบเสร็จ กรุณากรอกข้อมูลด้วยตนเอง';
                        }

                        resultHTML += '</div>';

                        // แสดงรายละเอียดข้อมูลที่ดึงได้
                        if (Object.values(data.data).some(val => val !== null)) {
                            resultHTML += '<div class="card mb-3"><div class="card-header bg-light"><h6 class="mb-0"><i class="fas fa-file-invoice me-2"></i>ข้อมูลที่ดึงได้จากใบเสร็จ</h6></div><div class="card-body">';
                            resultHTML += '<table class="table table-sm">';
                            resultHTML += '<tr><th style="width: 40%;">วันที่:</th><td>' + (data.data.date || '<span class="text-muted">ไม่พบ</span>') + '</td></tr>';
                            resultHTML += '<tr><th>จำนวนเงิน:</th><td>' + (data.data.total_amount ? data.data.total_amount.toLocaleString('th-TH', {style: 'currency', currency: 'THB'}) : '<span class="text-muted">ไม่พบ</span>') + '</td></tr>';
                            resultHTML += '<tr><th>ชื่อร้านค้า:</th><td>' + (data.data.vendor || '<span class="text-muted">ไม่พบ</span>') + '</td></tr>';
                            resultHTML += '<tr><th>เลขที่ใบเสร็จ:</th><td>' + (data.data.receipt_no || '<span class="text-muted">ไม่พบ</span>') + '</td></tr>';
                            resultHTML += '</table>';
                            resultHTML += '</div></div>';

                            // คำแนะนำการแก้ไขข้อมูล
                            resultHTML += '<div class="alert alert-info"><i class="fas fa-lightbulb me-2"></i><strong>คำแนะนำ:</strong> คุณสามารถแก้ไขข้อมูลที่ดึงได้หากพบว่าไม่ถูกต้อง</div>';
                        }

                        ocrResultsContainer.innerHTML = resultHTML;
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