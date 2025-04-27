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
        // Handle OCR upload button click - ต้องระบุ type="button" ในปุ่ม
        ocrUploadBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            // สร้าง input แบบชั่วคราวเพื่อเลือกไฟล์แทน
            const tempFileInput = document.createElement('input');
            tempFileInput.type = 'file';
            tempFileInput.accept = 'image/*';
            tempFileInput.style.display = 'none';
            document.body.appendChild(tempFileInput);
            
            tempFileInput.addEventListener('change', function() {
                if (this.files && this.files[0]) {
                    // Process the file with OCR
                    handleOCRFile(this.files[0]);
                    
                    // Copy the file to the receipt input in the form
                    const dt = new DataTransfer();
                    dt.items.add(this.files[0]);
                    receiptInput.files = dt.files;
                }
                // Remove the temporary input
                document.body.removeChild(tempFileInput);
            });
            
            // Trigger click on the temporary file input
            tempFileInput.click();
        });

        // Handle regular file input change (just for preview)
        receiptInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                showReceiptPreview(this.files[0]);
            }
        });
        
        // Function to show receipt preview
        function showReceiptPreview(file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                receiptPreview.src = e.target.result;
                receiptPreview.style.display = 'block';
                receiptPreview.parentElement.style.display = 'block';
            };
            reader.readAsDataURL(file);
        }
        
        // Function to handle file for OCR processing
        function handleOCRFile(file) {
            // Show loading indicator
            if (ocrLoadingIndicator) {
                ocrLoadingIndicator.style.display = 'block';
            }

            // Clear previous results
            if (ocrResultsContainer) {
                ocrResultsContainer.innerHTML = `
                    <div class="alert alert-info">
                        <div class="d-flex align-items-center">
                            <div class="spinner-border spinner-border-sm me-2" role="status">
                                <span class="visually-hidden">กำลังประมวลผล...</span>
                            </div>
                            <span>กำลังวิเคราะห์ใบเสร็จ กรุณารอสักครู่...</span>
                        </div>
                    </div>
                `;
                ocrResultsContainer.style.display = 'block';
            }

            // Show preview
            showReceiptPreview(file);

            // Process OCR
            processOCR(file);
        }

        // Process OCR
        function processOCR(file) {
            const formData = new FormData();
            formData.append('receipt', file);

            console.log('Starting OCR processing for file:', file.name);

            fetch('/api/ocr/receipt', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                console.log('OCR API response status:', response.status);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('OCR API response data:', data);

                // Hide loading indicator
                if (ocrLoadingIndicator) {
                    ocrLoadingIndicator.style.display = 'none';
                }

                if (data.success) {
                    // Log the full data object for debugging
                    console.log('Full OCR data object:', data);
                    
                    // Fill form fields with extracted data
                    if (data.data) {
                        // Debug log each field
                        console.log('Total amount:', data.data.total_amount);
                        console.log('Date:', data.data.date);
                        console.log('Vendor:', data.data.vendor);
                        console.log('Receipt number:', data.data.receipt_no || data.data.receipt_number);

                        // Set amount if available
                        if (data.data.total_amount !== null && data.data.total_amount !== undefined && amountInput) {
                            // Convert to number and format to 2 decimal places if needed
                            const amount = parseFloat(data.data.total_amount);
                            amountInput.value = isNaN(amount) ? '' : amount.toFixed(2);
                            console.log('Set amount input to:', amountInput.value);
                        }

                        // Set date if available
                        if (data.data.date && dateInput) {
                            dateInput.value = data.data.date;
                            console.log('Set date input to:', data.data.date);
                        }

                        // Set description with vendor and receipt number if available
                        if (descriptionInput) {
                            let description = '';
                            
                            if (data.data.vendor) {
                                description += data.data.vendor;
                            }
                            
                            // Add receipt number if available
                            const receiptNo = data.data.receipt_no || data.data.receipt_number;
                            if (receiptNo) {
                                description += ` (เลขที่: ${receiptNo})`;
                            }
                            
                            if (description) {
                                descriptionInput.value = description;
                                console.log('Set description input to:', description);
                            }
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
                        else if (data.data && Object.values(data.data).some(val => val !== null)) {
                            resultHTML += 'alert-success"><i class="fas fa-check-circle me-2"></i><strong>ดึงข้อมูลสำเร็จ</strong>';
                        }
                        // ถ้าไม่มีข้อมูลใดเลย แต่ยังถือว่าสำเร็จในการประมวลผล
                        else {
                            resultHTML += 'alert-info"><i class="fas fa-info-circle me-2"></i><strong>ประมวลผลสำเร็จ</strong> แต่ไม่พบข้อมูลจากใบเสร็จ กรุณากรอกข้อมูลด้วยตนเอง';
                        }

                        resultHTML += '</div>';

                        // แสดงรายละเอียดข้อมูลที่ดึงได้
                        if (data.data && Object.values(data.data).some(val => val !== null && val !== undefined)) {
                            resultHTML += '<div class="card mb-3"><div class="card-header bg-light"><h6 class="mb-0"><i class="fas fa-file-invoice me-2"></i>ข้อมูลที่ดึงได้จากใบเสร็จ</h6></div><div class="card-body">';
                            resultHTML += '<table class="table table-sm">';
                            
                            const displayValue = (value) => {
                                if (value === null || value === undefined) return '<span class="text-muted">ไม่พบ</span>';
                                return value;
                            };
                            
                            resultHTML += '<tr><th style="width: 40%;">วันที่:</th><td>' + displayValue(data.data.date) + '</td></tr>';
                            
                            // Format amount with Thai Baht currency if available
                            if (data.data.total_amount) {
                                const amount = parseFloat(data.data.total_amount);
                                const formattedAmount = isNaN(amount) 
                                    ? data.data.total_amount 
                                    : amount.toLocaleString('th-TH', {style: 'currency', currency: 'THB'});
                                resultHTML += '<tr><th>จำนวนเงิน:</th><td>' + formattedAmount + '</td></tr>';
                            } else {
                                resultHTML += '<tr><th>จำนวนเงิน:</th><td><span class="text-muted">ไม่พบ</span></td></tr>';
                            }
                            
                            resultHTML += '<tr><th>ชื่อร้านค้า:</th><td>' + displayValue(data.data.vendor) + '</td></tr>';
                            
                            // Use receipt_no or receipt_number, whichever is available
                            const receiptNo = data.data.receipt_no || data.data.receipt_number;
                            resultHTML += '<tr><th>เลขที่ใบเสร็จ:</th><td>' + displayValue(receiptNo) + '</td></tr>';
                            
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
                    console.error('OCR API returned error:', data.error);
                    if (ocrResultsContainer) {
                        ocrResultsContainer.innerHTML = `
                            <div class="alert alert-danger">
                                <p><i class="fas fa-exclamation-circle me-2"></i><strong>เกิดข้อผิดพลาด:</strong> ${data.error || 'ไม่สามารถประมวลผลใบเสร็จได้'}</p>
                                <p>กรุณากรอกข้อมูลด้วยตนเอง</p>
                                <p class="mt-2 small">หมายเหตุ: รูปภาพใบเสร็จได้ถูกบันทึกแล้ว แต่ไม่สามารถดึงข้อมูลได้โดยอัตโนมัติ</p>
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
                            <p><i class="fas fa-exclamation-circle me-2"></i><strong>เกิดข้อผิดพลาด:</strong> ${error.message || 'ไม่สามารถประมวลผลใบเสร็จได้'}</p>
                            <p>กรุณากรอกข้อมูลด้วยตนเอง</p>
                            <details class="mt-2">
                                <summary class="text-muted small">รายละเอียดเพิ่มเติม (สำหรับนักพัฒนา)</summary>
                                <pre class="small mt-2 p-2 bg-light">${error.stack || error}</pre>
                            </details>
                        </div>
                    `;
                    ocrResultsContainer.style.display = 'block';
                }

                // ให้ใบเสร็จยังแสดงอยู่ แม้จะมีข้อผิดพลาด
                if (receiptPreview) {
                    receiptPreview.style.display = 'block';
                    receiptPreview.parentElement.style.display = 'block';
                }
            });
        }
    }
});