// 숫자 입력만 허용하는 함수
function isNumber(event) {
    const charCode = event.which ? event.which : event.keyCode;
    // 숫자(48-57), 백스페이스(8), 탭(9), 엔터(13), 삭제(46), 방향키(37-40) 허용
    if (charCode >= 48 && charCode <= 57) {
        return true;
    }
    if (charCode == 8 || charCode == 9 || charCode == 13 || charCode == 46) {
        return true;
    }
    if (charCode >= 37 && charCode <= 40) {
        return true;
    }
    return false;
}

// 숫자 입력 필드 포맷팅 함수
function formatNumberInput(input) {
    // 현재 값에서 쉼표 제거
    let value = input.value.replace(/,/g, '');

    // 숫자만 남기기
    value = value.replace(/[^0-9]/g, '');

    // 빈 문자열이면 그대로 반환
    if (value === '') {
        input.value = '';
        return;
    }

    // 숫자를 천 단위로 쉼표 추가
    const numberValue = parseInt(value);
    input.value = numberValue.toLocaleString();
}

// 쉼표가 포함된 숫자 문자열을 숫자로 변환
function parseFormattedNumber(formattedString) {
    return parseFloat(formattedString.replace(/,/g, '')) || 0;
}

function eventHandlerPlaceholder() {


                // 탭 버튼 클릭 이벤트
                const tabButtons = document.querySelectorAll('.tab-button');
                const tabContents = document.querySelectorAll('.tab-content');

                tabButtons.forEach(button => {
                    button.addEventListener('click', function () {
                        tabButtons.forEach(btn => btn.classList.remove('active'));
                        tabContents.forEach(content => content.classList.remove('active'));
                        this.classList.add('active');
                        const tabId = this.getAttribute('data-tab');
                        document.getElementById(tabId).classList.add('active');
                    });
                });

                // 보수물량표의 단가 변경 시 개략공사비 업데이트
                const repairTable = document.querySelector('#repair .table-striped');
                if (repairTable) {
                    repairTable.addEventListener('input', function (e) {
                        if (e.target.matches('input[name^="unit_price_"]')
                            || e.target.matches('input[name^="repair_method_"]')
                            || e.target.matches('input[name^="priority_"]')
                        ) {
                            const row = e.target.closest('tr');
                            const quantity = parseFloat(row.cells[3].textContent);
                            // 콤마 제거 후 숫자로 변환
                            const unitPriceInput = row.querySelector('input[name^="unit_price_"]');
                            const unitPriceValue = unitPriceInput.value.replace(/,/g, '').trim();
                            const unitPrice = parseFloat(unitPriceValue);
                            const totalCostCell = row.querySelector('.total-cost');
                            const markupRate = document.getElementById('markup_rate').value;
                            const markupRateValue = 1+ parseFloat(markupRate.replace(/,/g, '').trim())/100;


                            if (totalCostCell) {
                                if (!isNaN(quantity) && !isNaN(unitPrice) && unitPriceValue !== '') {
                                    totalCostCell.textContent = Math.round(quantity * unitPrice * markupRateValue).toLocaleString();
                                } else {
                                    totalCostCell.textContent = '0';
                                }
                            }
                            updateCostTable();
                        }
                    });

                    // 단가 input 포커스 이벤트
                    repairTable.addEventListener('focus', function (e) {
                        if (e.target.matches('input[name^="unit_price_"]')) {
                            // 포커스 시 콤마 제거
                            e.target.value = e.target.value.replace(/,/g, '');
                        }
                    }, true);

                    // 단가 input 블러 이벤트
                    repairTable.addEventListener('blur', function (e) {
                        if (e.target.matches('input[name^="unit_price_"]')) {
                            // 블러 시 콤마 추가
                            const cleanValue = e.target.value.replace(/,/g, '').trim();
                            const value = parseFloat(cleanValue);

                            if (!isNaN(value) && cleanValue !== '') {
                                // input 타입이 number인 경우 콤마 없는 값을 설정
                                if (e.target.type === 'number') {
                                    e.target.value = value;
                                } else {
                                    // input 타입이 text인 경우 콤마 포함된 값을 설정
                                    e.target.value = value.toLocaleString();
                                }
                            } else {
                                // 비어있거나 유효하지 않은 값인 경우 0으로 설정
                                e.target.value = '0';
                            }
                        }
                    }, true);

                    // 단가 input keyup 이벤트 (실시간 검증)
                    repairTable.addEventListener('keyup', function (e) {
                        if (e.target.matches('input[name^="unit_price_"]')) {
                            const cleanValue = e.target.value.replace(/,/g, '').trim();

                            // 빈 값이거나 숫자가 아닌 경우 처리하지 않음 (사용자가 입력 중일 수 있음)
                            if (cleanValue === '') {
                                // 빈 값일 때는 totalCost를 0으로 업데이트
                                const row = e.target.closest('tr');
                                const totalCostCell = row.querySelector('.total-cost');
                                if (totalCostCell) {
                                    totalCostCell.textContent = '0';
                                }
                            }
                        }
                    });
                }

                // 경간생성 버튼 이벤트 리스너
                const generateSpansBtn = document.getElementById('generateSpans');
                if (generateSpansBtn) {
                    generateSpansBtn.addEventListener('click', function() {
                        const spanCount = parseInt(document.getElementById('spanCount').value);
                        if (isNaN(spanCount) || spanCount < 1) {
                            alert('유효한 경간 수를 입력해주세요.');
                            return;
                        }
                        generateSpans(spanCount);
                    });
                }

}

document.addEventListener('DOMContentLoaded', function () {
    eventHandlerPlaceholder();
});



function updateCostTable() {
    const repairTable = document.querySelector('#repair .table-striped');
    if (!repairTable) return;

    // 서버 로직과 동일하게 그룹화: ['부재명', '보수방안', '우선순위']
    const costByGroup = {};
    const rows = repairTable.querySelectorAll('tbody tr');

    rows.forEach(row => {
        const component = row.cells[0].textContent;
        const damageContent = row.cells[1].textContent;
        const method = row.querySelector('input[name^="repair_method_"]').value;
        const priority = row.querySelector('input[name^="priority_"]').value;
        const quantity = parseFloat(row.cells[3].textContent);
        const unitPrice = parseFloat(row.querySelector('input[name^="unit_price_"]').value.replace(/,/g, ''));

        // 주의관찰은 제외 (서버 로직과 동일)
        if (!method || !priority || isNaN(quantity) || isNaN(unitPrice) || method === '주의관찰') return;

        const groupKey = `${component}_${method}_${priority}`;
        if (!costByGroup[groupKey]) {
            costByGroup[groupKey] = {
                component: component,
                damageContents: new Set(),
                method: method,
                priority: priority,
                quantity: 0,
                count: 0,
                unitPrice: unitPrice,
                totalCost: 0
            };
        }

        // 손상내용을 Set에 추가 (중복 제거)
        costByGroup[groupKey].damageContents.add(damageContent);
        costByGroup[groupKey].quantity += quantity;
        costByGroup[groupKey].count += 1;
        costByGroup[groupKey].totalCost += quantity * unitPrice;
    });

    // 개략공사비표 업데이트 - 기존 구조 유지하면서 데이터만 업데이트
    const costTable = document.querySelector('#cost .table-striped tbody');
    if (!costTable) return;

    // 모든 기존 행 제거 (헤더는 유지)
    const existingRows = costTable.querySelectorAll('tr');
    existingRows.forEach(row => {
        row.remove();
    });

    // 서버 로직과 동일하게 그룹화된 데이터로 행 생성
    Object.values(costByGroup).forEach(item => {
        const row = document.createElement('tr');
        // 손상내용을 정렬된 문자열로 병합 (서버 로직과 동일)
        const damageContentStr = Array.from(item.damageContents).sort().join(', ');

        row.innerHTML = `
            <td>${item.component}</td>
            <td>${damageContentStr}</td>
            <td>${item.method}</td>
            <td>${item.priority}</td>
            <td>${item.quantity.toFixed(2)}</td>
            <td>${item.count}</td>
            <td>${item.unitPrice.toLocaleString()}</td>
            <td>${Math.round(item.totalCost).toLocaleString()}</td>
        `;
        costTable.appendChild(row);
    });


    // 총계 행은 표시하지 않음
}

function saveCostTable() {
    console.log('보수물량 저장 기능 실행');
    const repairTable = document.querySelector('#repair .table-striped');
    if (!repairTable) {
        console.error('#repair .table-striped 요소를 찾을 수 없음');
        return;
    }

    // 로딩 오버레이 표시
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.style.display = 'flex';
        console.log('로딩 오버레이 표시됨');
    }

    const repairData = {};
    const rows = repairTable.querySelectorAll('tbody tr');

    console.log('총 ' + rows.length + '개의 공사 데이터 행 처리');

    rows.forEach((row, index) => {
        try {
        const component = row.cells[0].textContent;
        const damage = row.cells[1].textContent;
        const unit = row.cells[2].textContent;
            const damage_quantity = parseFloat(row.cells[3].textContent);
            const quantityCell = row.cells[4];
            const quantity = parseFloat(quantityCell.getAttribute('notadd'));

            const count = parseInt(row.cells[5].textContent);
        const method = row.querySelector('input[name^="repair_method_"]').value;
        const priority = row.querySelector('input[name^="priority_"]').value;
        const unitPrice = parseFloat(row.querySelector('input[name^="unit_price_"]').value.replace(/,/g, ''));
            const totalCost = parseFloat(row.querySelector('.total-cost').textContent.replace(/,/g, ''));

            if (!method || !priority || isNaN(quantity) || isNaN(unitPrice)) {
                console.warn('행 ' + index + '의 데이터가 불완전하여 건너띔');
                return;
            }

            const key = `row_${index}`;
            repairData[key] = {
                component: component,
                damage: damage,
                unit: unit,
                damage_quantity: damage_quantity,
                quantity: quantity,
                count: count,
                method: method,
                priority: priority,
                unitPrice: unitPrice,
                totalCost: totalCost
            };
            console.log('행 ' + index + ' 데이터 처리:', repairData[key]);
        } catch (error) {
            console.error('행 ' + index + ' 처리 중 오류:', error);
        }
    });

    console.log('전송할 데이터:', repairData);

    if (Object.keys(repairData).length === 0) {
        alert('저장할 데이터가 없습니다.');
        if (loadingOverlay) loadingOverlay.style.display = 'none';
        return;
    }

    // 서버로 데이터 전송
    fetch('/files/update_file_damage_details', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(repairData)
    })
    .then(response => {
        console.log('서버 응답 상태:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('서버 응답 데이터:', data);
        // 스낵바 표시
        const snackbar = document.getElementById('snackbar');
        if (snackbar) {
            snackbar.className = 'show';
            setTimeout(() => { snackbar.className = snackbar.className.replace('show', ''); }, 3000);
        }

        // 응답에 HTML 데이터가 있으면 화면 업데이트
        if (data.repair_html) {
            document.getElementById('repair_html').innerHTML = data.repair_html;
        }
        if (data.cost_html) {
            document.getElementById('cost_html').innerHTML = data.cost_html;
        }
    })
    .catch(error => {
        console.error('데이터 저장 중 오류 발생:', error);
        alert('데이터 저장 중 오류가 발생했습니다.');
    })
    .finally(() => {
        // 로딩 오버레이 숨김
        if (loadingOverlay) {
            loadingOverlay.style.display = 'none';
            console.log('로딩 오버레이 숨김');
        }
         eventHandlerPlaceholder();
         initRepairMethodDropdown();
    });
}

var bo_pivot = true;
var bo_detail = false;
// 페이지 로드 시 btn_pivot 버튼이 있는지 확인
document.addEventListener('DOMContentLoaded', function() {
    const pivotButton = document.getElementById('btn_pivot');
    if (pivotButton) {
        // 피봇 버튼 이벤트 리스너 등록
        pivotButton.addEventListener('click', function () {
            console.log('피봇 버튼 클릭됨');
            const loadingOverlay = document.getElementById('loading-overlay');
            if (loadingOverlay) {
                loadingOverlay.style.display = 'flex';
                console.log('로딩 오버레이 표시됨');
            }
            bo_pivot = !bo_pivot;

            const formData = {
                pivot: bo_pivot,detail: bo_detail
            };

            console.log('피봇 요청 데이터:', formData);
             fetch("/data/pivot_detail", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(formData)
            })
            .then(res => {
                console.log('응답 상태:', res.status);
                return res.json();
            })
            .then(data => {
                console.log('피봇 데이터 수신됨:', data);
                if (data.detail_html) {
                    const detailContainer = document.querySelector("#detail .table-responsive");
                    if (detailContainer) {
                        detailContainer.innerHTML = data.detail_html;
                        console.log('상세 테이블 업데이트됨');
                    } else {
                        console.error('#detail .table-responsive 요소를 찾을 수 없음');
                    }

                } else {
                    console.error('detail_html 데이터가 없음:', data);
                }
            })
            .catch(error => {
                console.error('피봇 요청 중 오류 발생:', error);
            })
            .finally(() => {
                if (loadingOverlay) {
                    loadingOverlay.style.display = 'none';
                    console.log('로딩 오버레이 숨김');
                }
            });
        });
    } else {
        console.warn('피봇 버튼(#btn_pivot)을 찾을 수 없음');
    }




    // 균열 세분화 버튼 이벤트 리스너 등록
    const crackDetailButton = document.getElementById('btn_crack_detail');
    if (crackDetailButton) {
        crackDetailButton.addEventListener('click', function () {
            console.log('균열 세분화 버튼 클릭됨');

            // 로딩 오버레이 표시
            const loadingOverlay = document.getElementById('loading-overlay');
            if (loadingOverlay) {
                loadingOverlay.style.display = 'flex';
            }
            bo_detail = !bo_detail;


            const formData = {
                pivot: bo_pivot , detail: bo_detail,
            };


            // 균열 세분화 처리 요청
            fetch('/data/crack_subdivision', {
                   method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(data => {
                 if (data.detail_html) {
                    const detailContainer = document.querySelector("#detail .table-responsive");
                    if (detailContainer) {
                        detailContainer.innerHTML = data.detail_html;
                        console.log('균열 세분화 테이블 업데이트됨');
                    }
                } else if (data.error) {
                    alert('균열 세분화 처리 중 오류가 발생했습니다: ' + data.error);
                }
            })
            .catch(error => {
                console.error('균열 세분화 요청 중 오류:', error);
                alert('균열 세분화 요청 중 오류가 발생했습니다.');
            })
            .finally(() => {
                if (loadingOverlay) {
                    loadingOverlay.style.display = 'none';
                }
            });
        });
    } else {
        console.warn('균열 세분화 버튼(#btn_crack_detail)을 찾을 수 없음');
    }
});

// 페이지 로드 시 저장된 데이터 불러오기
window.addEventListener('load', function () {
    const savedData = localStorage.getItem('bridgeEvaluationData');
    if (savedData) {
        const formData = JSON.parse(savedData);
        Object.keys(formData).forEach(key => {
            const element = document.getElementById(key);
            if (element) {
                element.value = formData[key];
            }
        });
    }
});

// 부재별 집계표 변경 시 상태평가 업데이트
document.querySelector('#detail .table-striped').addEventListener('change', function () {
    generateSpans(this.value);
});

document.getElementById("updateRepairBtn")?.addEventListener("click", function () {
    const rows = document.querySelectorAll("#repair .repair-table tbody tr");
    const repairData = [];
    rows.forEach(row => {
        const cells = row.querySelectorAll("td");
        const component = cells[0].textContent;
        const damage = cells[1].textContent;
        const quantity = parseFloat(cells[3].textContent);
        const count = parseInt(cells[4].textContent);
        const method = row.querySelector("input[name^='repair_method_']").value;
        const priority = row.querySelector("input[name^='priority_']").value;
        const unitPrice = parseFloat(row.querySelector("input[name^='unit_price_']").value.replace(/,/g, ''));

        repairData.push({
            component, damage, quantity, count,
            repairMethod: method, priority, unitPrice
        });
    });

    fetch("/data/update_repair", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(repairData)
    })
        .then(res => res.json())
        .then(data => {
            document.querySelector("#cost .table-responsive").innerHTML = data.cost_table + data.cost_summary;
        });
});


function initRepairMethodDropdown() {



    function initializeRepairMethodSelect() {
        const repairTable = document.querySelector('#repair .table-striped tbody');
        if (!repairTable) return;

        const repairMethods = new Set();
        const rows = repairTable.querySelectorAll('tr');

        rows.forEach(row => {
            const methodInput = row.querySelector('input[name^="repair_method_"]');
            if (methodInput && methodInput.value) {
                repairMethods.add(methodInput.value);
            }
        });

        const select = document.getElementById('repairMethodSelect');
        if (select) {
            // 기존 옵션 제거 (첫 번째 옵션 제외)
            while (select.children.length > 1) {
                select.removeChild(select.lastChild);
            }

            // 보수방안 옵션 추가
            Array.from(repairMethods).sort().forEach(method => {
                const option = document.createElement('option');
                option.value = method;
                option.textContent = method;
                select.appendChild(option);
            });
        }
    }

    // 보수방안 선택 시 해당 보수방안의 현재 단가 표시
    document.getElementById('repairMethodSelect')?.addEventListener('change', function() {
        const selectedMethod = this.value;
        const unitPriceInput = document.getElementById('unitPriceInput');

        if (selectedMethod) {
            // 해당 보수방안의 첫 번째 단가를 가져와서 표시
            const repairTable = document.querySelector('#repair .table-striped tbody');
            const rows = repairTable.querySelectorAll('tr');

            for (let row of rows) {
                const methodInput = row.querySelector('input[name^="repair_method_"]');
                if (methodInput && methodInput.value === selectedMethod) {
                    const unitPriceInputInRow = row.querySelector('input[name^="unit_price_"]');
                    if (unitPriceInputInRow) {
                        unitPriceInput.value = unitPriceInputInRow.value.replace(/,/g, '');
                        break;
                    }
                }
            }
        } else {
            unitPriceInput.value = '';
        }
    });

    // 단가 일괄 수정 버튼 클릭 이벤트
    document.getElementById('updateUnitPriceBtn')?.addEventListener('click', function() {
        const selectedMethod = document.getElementById('repairMethodSelect').value;
        const newUnitPrice = document.getElementById('unitPriceInput').value;

        if (!selectedMethod) {
            alert('보수방안을 선택해주세요.');
            return;
        }

        if (!newUnitPrice || isNaN(newUnitPrice) || parseFloat(newUnitPrice) < 0) {
            alert('올바른 단가를 입력해주세요.');
            return;
        }

        // 해당 보수방안의 모든 행의 단가를 업데이트
        const repairTable = document.querySelector('#repair .table-striped tbody');
        const rows = repairTable.querySelectorAll('tr');
        let updatedCount = 0;

        rows.forEach(row => {
            const methodInput = row.querySelector('input[name^="repair_method_"]');
            if (methodInput && methodInput.value === selectedMethod) {
                const unitPriceInput = row.querySelector('input[name^="unit_price_"]');
                if (unitPriceInput) {
                    // 숫자 값을 그대로 설정 (toLocaleString 사용하지 않음)
                    unitPriceInput.value = parseFloat(newUnitPrice);
                    updatedCount++;

                    // 총 공사비 업데이트
                    const quantity = parseFloat(row.cells[4].getAttribute('notadd') || row.cells[4].textContent);
                    const totalCost = quantity * parseFloat(newUnitPrice);
                    const totalCostElement = row.querySelector('.total-cost');
                    if (totalCostElement) {
                        totalCostElement.textContent = totalCost.toLocaleString();
                    }
                }
            }
        });

        if (updatedCount > 0) {
            alert(`${selectedMethod} 보수방안의 ${updatedCount}개 항목의 단가가 ${parseFloat(newUnitPrice).toLocaleString()}원으로 변경되었습니다.`);

            // 개략공사비표 업데이트
            updateCostTable();
        } else {
            alert('해당 보수방안의 항목을 찾을 수 없습니다.');
        }
    });

    // 보수물량표가 로드될 때마다 보수방안 드롭다운 초기화
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList' && mutation.target.id === 'repair_html') {
                setTimeout(initializeRepairMethodSelect, 100);
            }
        });
    });

    const repairContainer = document.getElementById('repair_html');
    if (repairContainer) {
        observer.observe(repairContainer, { childList: true, subtree: true });
        // 초기 로드 시에도 실행
        setTimeout(initializeRepairMethodSelect, 500);
    }


}



// 보수방안별 일괄 단가 수정 기능
document.addEventListener('DOMContentLoaded', function() {
    // 보수방안 드롭다운 초기화
    initRepairMethodDropdown();
});



// 경간 생성 함수
function generateSpans(spanCount) {
    const tbody = document.getElementById('evaluationResults');
    if (!tbody) {
        console.error('evaluationResults element not found');
        return;
    }

    tbody.innerHTML = '';
    const structureType = document.getElementById('structureType').value;

    // 기본 데이터 구조 생성
    const spans = [];
    spans.push('A1(S1)');
    for (let i = 1; i < spanCount; i++) {
        spans.push(`P${i}(S${i + 1})`);
    }
    spans.push('A2');

    spans.forEach((span, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${span}</td>
            <td>${structureType}</td>
            <td>b</td>
            <td>b</td>
            <td>b</td>
            <td>b</td>
            <td>a</td>
            <td>b</td>
            <td>b</td>
            <td>b</td>
            <td>b</td>
            <td>b</td>
            <td>b</td>
        `;
        tbody.appendChild(row);
    });

    // 상태평가 업데이트
    updateEvaluationTable();
}

function updateEvaluationTable() {
    const table = document.querySelector('#detail .table-striped');
    if (table) {
        const event = new Event('change');
        table.dispatchEvent(event);
    }
}

// 저장 버튼 클릭 이벤트
document.getElementById('saveData')?.addEventListener('click', function () {
    const formData = {
        bridgeName: document.getElementById('bridgeName').value,
        length: document.getElementById('length').value,
        width: document.getElementById('width').value,
        structureType: document.getElementById('structureType').value,
        spanCount: document.getElementById('spanCount').value,
        expansionJoint: document.getElementById('expansionJoint').value,
        girderArea: document.getElementById('girderArea').value,
        crossbeamArea: document.getElementById('crossbeamArea').value,
        abutmentArea: document.getElementById('abutmentArea').value,
        pierArea: document.getElementById('pierArea').value
    };

    // 로컬 스토리지에 저장
    localStorage.setItem('bridgeEvaluationData', JSON.stringify(formData));
    alert('데이터가 저장되었습니다.');
});

// jQuery 코드는 jQuery와 문서가 모두 준비된 후 실행
function initJQueryFeatures() {
    if (typeof $ === 'undefined') {
        console.warn('jQuery가 아직 로드되지 않았습니다. 0.1초 후 재시도합니다.');
        setTimeout(initJQueryFeatures, 100);
        return;
    }

    $(document).ready(function() {
        // 네비게이션 클릭 이벤트 처리 (외관조사보고서)
        $(document).on('click', '.sticky-header a[href^="#"]', function(e) {
        e.preventDefault();

        const targetId = $(this).attr('href');
        // ID에서 # 제거하고 안전하게 선택
        const cleanId = targetId.substring(1);

        // 특수문자가 포함된 ID를 안전하게 처리
        const safeId = cleanId.replace(/[^a-zA-Z0-9_-]/g, '_');

        // 여러 방법으로 요소 찾기
        let finalElement = $(`#${cleanId}`); // 원본 ID로 시도

        if (finalElement.length === 0) {
            finalElement = $(`#${safeId}`); // 안전한 ID로 시도
        }

        if (finalElement.length === 0) {
            // 부재명으로 직접 찾기 (h4 태그의 텍스트 내용으로)
            const componentName = cleanId.replace('header_', '');
            finalElement = $(`h4:contains("📌 부재명: ${componentName}")`);
        }

        if (finalElement.length === 0) {
            // 더 유연한 검색: 부재명의 일부만 포함되어도 찾기
            const componentName = cleanId.replace('header_', '');
            finalElement = $(`h4[id*="${componentName}"]`);
        }

        console.log(`클릭된 링크: ${targetId}, 정리된 ID: ${cleanId}, 안전한 ID: ${safeId}, 찾은 요소:`, finalElement);

        if (finalElement.length > 0) {
            // 모든 네비게이션 버튼에서 active 클래스 제거
            $('.sticky-header a').removeClass('active');

            // 클릭된 버튼에 active 클래스 추가
            $(this).addClass('active');

            // 탭 네비게이션으로 이동하는 경우와 부재 제목으로 이동하는 경우를 구분
            let scrollOffset;
            if (targetId === '#tab-navigation') {
                // 탭 네비게이션으로 이동하는 경우
                scrollOffset = 100;
            } else {
                // 부재 제목으로 이동하는 경우
                scrollOffset = 146;
            }

            // 부드러운 스크롤로 해당 요소로 이동
            $('html, body').animate({
                scrollTop: finalElement.offset().top - scrollOffset
            }, 500);

            // 잠시 후 active 클래스 제거 (시각적 피드백)
            setTimeout(() => {
                $(this).removeClass('active');
            }, 1000);

            console.log(`외관조사보고서 네비게이션 클릭: ${targetId}로 이동`);
        } else {
            console.log(`요소를 찾을 수 없습니다: ${targetId}`);
        }
    });

    // 스크롤 시 현재 보이는 섹션에 따라 네비게이션 버튼 활성화 (외관조사보고서)
    $(window).on('scroll', function() {
        const scrollTop = $(window).scrollTop();

        // 각 부재 섹션의 위치 확인
        const sections = [];
        $('h4[id^="header_"]').each(function() {
            sections.push($(this).attr('id'));
        });

        // 탭 네비게이션도 섹션에 추가
        sections.push('tab-navigation');

        let activeSection = '';

        sections.forEach(sectionId => {
            const element = $(`#${sectionId}`);
            if (element.length > 0) {
                const elementTop = element.offset().top;
                const elementBottom = elementTop + element.outerHeight();

                // 현재 스크롤 위치가 해당 섹션 내에 있는지 확인
                if (scrollTop + 200 >= elementTop && scrollTop + 200 <= elementBottom) {
                    activeSection = sectionId;
                }
            }
        });

        // 네비게이션 버튼 활성화 상태 업데이트
        $('.sticky-header a').removeClass('active');
        if (activeSection) {
            $(`.sticky-header a[href="#${activeSection}"]`).addClass('active');
        }
    });
    });
}

// 제경비율 저장 함수
function saveOverheadRate(filename) {
    const overheadRate = document.getElementById('overhead_rate').value;

    if (!overheadRate || isNaN(overheadRate)) {
        alert('유효한 제경비율을 입력해주세요.');
        return;
    }

    const rate = parseFloat(overheadRate);
    if (rate < 0 || rate > 1000) {
        alert('제경비율은 0~1000% 범위여야 합니다.');
        return;
    }

    // 서버에 제경비율 저장 요청
    fetch('/api/save_overhead_rate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            filename: filename,
            overhead_rate: rate
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.message);
            // 보수물량표와 개략공사비표 다시 로드
            reloadRepairAndCostTables(filename);
            initRepairMethodDropdown();
        } else {
            alert('제경비율 저장 실패: ' + data.error);
        }
    })
    .catch(error => {
        console.error('제경비율 저장 중 오류:', error);
        alert('제경비율 저장 중 오류가 발생했습니다.');
    });
}

// 할증율 저장 함수
function saveMarkupRate(filename) {
    const markupRate = document.getElementById('markup_rate').value;

    if (!markupRate || isNaN(markupRate)) {
        alert('유효한 할증율을 입력해주세요.');
        return;
    }

    const rate = parseFloat(markupRate);
    if (rate < 0 || rate > 100) {
        alert('할증율은 0~100% 범위여야 합니다.');
        return;
    }

    // 서버에 할증율 저장 요청
    fetch('/api/save_markup_rate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            filename: filename,
            markup_rate: rate
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.message);
            // 보수물량표와 개략공사비표 다시 로드
            reloadRepairAndCostTables(filename);
            initRepairMethodDropdown();
        } else {
            alert('할증율 저장 실패: ' + data.error);
        }
    })
    .catch(error => {
        console.error('할증율 저장 중 오류:', error);
        alert('할증율 저장 중 오류가 발생했습니다.');
    });
}

// 부대공사비 저장 함수
function saveSubsidiaryCost(filename) {
    const subsidiaryCostInput = document.getElementById('subsidiary_cost').value;

    if (!subsidiaryCostInput) {
        alert('부대공사비를 입력해주세요.');
        return;
    }

    // 쉼표가 포함된 숫자 문자열을 숫자로 변환
    const cost = parseFormattedNumber(subsidiaryCostInput);

    if (isNaN(cost) || cost < 0) {
        alert('유효한 부대공사비를 입력해주세요. (0원 이상)');
        return;
    }

    // 서버에 부대공사비 저장 요청
    fetch('/api/save_subsidiary_cost', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            filename: filename,
            subsidiary_cost: cost
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.message);
            // 보수물량표와 개략공사비표 다시 로드
            reloadRepairAndCostTables(filename);
            initRepairMethodDropdown();
        } else {
            alert('부대공사비 저장 실패: ' + data.error);
        }
    })
    .catch(error => {
        console.error('부대공사비 저장 중 오류:', error);
        alert('부대공사비 저장 중 오류가 발생했습니다.');
    });
}

// 보수물량표와 개략공사비표 재로드 함수
function reloadRepairAndCostTables(filename) {
    console.log('테이블 재로드 시작:', filename);

    fetch('/api/reload_repair_table', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            filename: filename
        })
    })
    .then(response => {
        console.log('서버 응답 상태:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('서버 응답 데이터:', data);

        if (data.success) {
            console.log('테이블 재로드 성공');

            // 보수물량표 업데이트
            const repairContainer = document.getElementById('repair_html');
            if (repairContainer && data.repair_html) {
                console.log('보수물량표 HTML 업데이트 중...');
                repairContainer.innerHTML = data.repair_html;
                console.log('보수물량표 HTML 업데이트 완료');
            } else {
                console.warn('보수물량표 컨테이너를 찾을 수 없거나 HTML 데이터가 없음:', {
                    container: !!repairContainer,
                    html: !!data.repair_html
                });
            }

            // 개략공사비표 업데이트
            const costContainer = document.getElementById('cost_html');
            if (costContainer && data.cost_html) {
                console.log('개략공사비표 HTML 업데이트 중...');
                costContainer.innerHTML = data.cost_html;
                console.log('개략공사비표 HTML 업데이트 완료');
            } else {
                console.warn('개략공사비표 컨테이너를 찾을 수 없거나 HTML 데이터가 없음:', {
                    container: !!costContainer,
                    html: !!data.cost_html
                });
            }

            console.log('보수물량표와 개략공사비표가 업데이트되었습니다.');
            initRepairMethodDropdown();
        } else {
            console.error('테이블 재로드 실패:', data.error);
            alert('테이블 재로드 실패: ' + data.error);
        }
        eventHandlerPlaceholder();
    })
    .catch(error => {
        console.error('테이블 재로드 중 오류:', error);
        alert('테이블 재로드 중 오류가 발생했습니다: ' + error.message);
    });
}

// 할증율 변경 시 개략공사비 실시간 업데이트 (선택적 기능)
function updateCostByMarkupRate() {
    const markupRate = parseFloat(document.getElementById('markup_rate')?.value || 20);
    const costCells = document.querySelectorAll('.total-cost');

    costCells.forEach(cell => {
        const row = cell.closest('tr');
        const quantityCell = row.cells[4]; // 보수물량
        const unitPriceInput = row.querySelector('input[name^="unit_price_"]');

        if (quantityCell && unitPriceInput) {
            const quantity = parseFloat(quantityCell.textContent);
            const unitPrice = parseFloat(unitPriceInput.value.replace(/,/g, ''));

            if (!isNaN(quantity) && !isNaN(unitPrice)) {
                const baseCost = quantity * unitPrice;
                const totalCost = baseCost * (1 + markupRate / 100);
                cell.textContent = Math.round(totalCost).toLocaleString();
            }
        }
    });
}

// jQuery 기능 초기화 시작
initJQueryFeatures();
